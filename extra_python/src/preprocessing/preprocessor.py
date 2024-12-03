
from __future__ import print_function
import os
import json
import execnet
import time
import traceback
import uuid
import re
import collections
import string
import pandas as pd
from sklearn.model_selection import train_test_split
from utils import dataprep_utils
from preprocessing import tokenizer_plus
from config import custom_configparser


class SizeBounds(
    collections.namedtuple(
        "SizeBounds",
        ("srcLower",
         'srcUpper',
         'tgtLower',
         'tgtUpper'))):
    pass


class TokenizationParams(
    collections.namedtuple(
        "TokenizationParams",
        ('exclude_list',
         'split_identifiers',
         'split_strings'))):
    pass


config = custom_configparser.CustomConfigParser()

SRC = "nl"
TGT = "pl"
STRING_SEPARATOR = '|SEP|'


def overrides(parent_class):
    def overrider(method):
        assert(method.__name__ in dir(parent_class))
        return method
    return overrider


class Preprocessor(object):
    '''Preprocessor base class
    '''

    def __init__(self, repository,
                 dataset_loc,
                 model_name,
                 size_bounds=[5, 300, 5, 300],
                 origin_url=None):
        '''
        Constructor.
        Args:
            repository (str): path/url to the repository storing raw data
            datset_loc (str): path to local/alluxio/cloudant directory to store parsed datasets
            model_name (str): user-defined name of the model
            size_bounds (list): 4-item array [srcLower, srcUpper, tgtLower, tgtUpper]. Defaults to [5,300,5,300]
            origin_url(str): where  training data originated from

        Dependency jars can be  collected using jip.
        Navigate to pom.xml location and run
            pip install jip
            jip resolve pom.xm
        jip creates a directory called javalib and puts to it all jars specified in pom. The path to all the jars in javalib must be added to classpath
        '''

        self.repository = repository
        self.dataset_loc = dataset_loc
        self.model_name = model_name
        self.tokenization_params = TokenizationParams(
            **config.get_tokenization_params())

        self.size_bounds = SizeBounds(srcLower=size_bounds[0],
                                      srcUpper=size_bounds[1],
                                      tgtLower=size_bounds[2],
                                      tgtUpper=size_bounds[3])

        self.origin_url = origin_url

        self.classpath = config.get_java_classpath()
        self.jython_path = config.get_java_jythonpath()

        meta = {}
        meta["uuid"] = str(uuid.uuid4())
        meta["name"] = model_name
        meta["size_bounds"] = size_bounds
        self.meta = meta

    def run(self,
            non_duplicates=None,
            _filter=None,
            test_size=0.2,
            random_seed=None,
            multipunct_threshold=5):
        ''' Execute end-to-end preprocessing pipeline:
        - crawl software repository to retrieve test cases
        - parse retrieved code to extract features
        - synthetise source and target corpora
        - generate train and test sets
        - extract source and target vocabularies
        Args:
            non_duplicates: (set) set of unique source sentences to control duplicates. Sentences already in the set will be skipped.
            _filter (str): regex pattern. Sequences matching the pattern will be excluded from corpus. Example: '#method test [0-9]+$'
            test_size (double): size of the test set to be used when the splitting corpus into train and test sets
            random_seed (int) random seed for train- / testset split

        Returns:
            dict: dataset metadata containing the following information:
                - uuid : dataset_uuid
                - name: dataset/model name
                - add_comments whether comments were added to source sequences
                - size_bounds: max/min sequence lengths
                - parsed_size: number of parsed test cases
                - corpus_size: corpus size
                - trainset_size: training set size
                - vocab_nl_size: size of natural language vocab
                - vocab_pl_size: size of programming language vocab

        '''
        raw_docs = self.crawl_repository()
        print("raw_docs in python: %i" % len(raw_docs), flush=True)
        if not raw_docs:
            self.meta["parsed_size"] = 0
            return self.meta, non_duplicates

        self.create_dataset_dir()

        parsed_docs = self.parse_dataset(raw_docs)
        print("parsed_docs in python: %i" % len(parsed_docs), flush=True)
        for doc in parsed_docs:
            doc['rawClasses'] = None
            self.save_doc(doc)
        (corpus_src,
         corpus_tgt,
         corpus_ids,
         non_duplicates) = self.extract_corpora(parsed_docs,
                                                non_duplicates=non_duplicates,
                                                _filter=_filter,
                                                multipunct_threshold=multipunct_threshold)

        if len(corpus_src) > 0:
            self.save_dataset("corpus", SRC, corpus_src)
            self.save_dataset("corpus", TGT, corpus_tgt)
            self.save_dataset("corpus", "ids", corpus_ids)
            self.process_corpora(
                corpus_src,
                corpus_tgt,
                test_size=test_size,
                random_seed=random_seed)
        else:
            print("Extracted corpus is empty", flush=True)

        self.meta["parsed_size"] = len(parsed_docs)
        self.meta["corpus_size"] = len(corpus_src)
        self.meta['random_seed'] = random_seed
        self.meta['test_size'] = test_size
        self.meta['multipunct_threshold'] = multipunct_threshold
        self.save_meta()

        return self.meta, non_duplicates

    def create_dataset_dir(self):
        '''Must be implemented by subclasses
        '''
        pass

    def save_meta(self):
        '''Must be implemented by subclasses
        '''
        pass

    def save_doc(self, doc):
        '''Must be implemented by subclasses
        Args:
            doc (dict): test case parsed to json format
        '''
        pass

    def save_dataset(self, filename, suffix, dataset):
        '''Must be implemented by subclasses
        Args:
            filename (str): name of the dataset [corpus | train | dev | vocab]
            suffix (str): suffix indicating dataset purpose [src | tgt | ids]
            dataset (list): dataset split to lines
        '''
        pass

    def get_doc(self, _dir, doc_id):
        '''Must be implemented by subclasses
        Args:
            dir (str): immediate parent dir storing the document [parsed_data | corpora]
            doc_id (str): id of the document to retrieve
        Returns:
            str: the document as a single string (json string or corpus with lines separated by newline chars)

        '''
        pass

    def get_all_docs(self, _dir):
        '''Must be implemented by subclasses
        Args:
            dir (str): directory with contents to retrieve [pasrsed_data | corpora]
        Returns:
            dict: all documents from the directory in json format {"doc_id": "document_body"}
        '''
        pass
    
    def get_parsed_data(self):
        '''Must be implemented by subclasses
        '''
        pass

    def crawl_repository(self):
        '''Crawl repository, extract all text classes and save to local or alluxio location
        Returns:
            list: list of dict objects representing unparsed Java classes in json format
        '''
        test_classes = dataprep_utils.find_test_classes(self.repository)
        count = 0
        raw_docs = []
        for test_class in test_classes:
            doc = {}
            count += 1
            try:
                with open(test_class, encoding='utf-8') as f:
                    rawClass = {}
                    rawClass[test_class.split('/')[-1]] = f.read()
                    doc['rawClasses'] = [rawClass]
                    doc['origin_url'] = self.origin_url
                    doc['_id'] = '%s-%i' % (test_class.split('/')[-1], count)
                    doc['filepath'] = test_class
                    raw_docs.append(doc)
            except UnicodeDecodeError as e:
                print("%s : %s" % (e, test_class), flush=True)
        return raw_docs

    def parse_dataset(self, raw_docs):
        ''' Parse Java compilation units.
        Executed with Jython via execnet channel.
        Args:
            raw_docs: list of dict objects representing unparsed Java classes in json format
        Returns:
            list: list of dict object representing Java compilation units with parsed test cases
        '''
        os.environ["CLASSPATH"] = self.classpath
        group = execnet.Group()
        gw = group.makegateway("popen//python=%s" % self.jython_path)
        channel = gw.remote_exec("""
        raw_docs=channel.receive()
        from com.google.gson import Gson
        from preprocessing.utils import DataPrepUtils
        from preprocessing.obj import RawDocument
        import json
        gson=Gson()
        raw_docs_objects=[gson.fromJson(json.dumps(d),RawDocument) for d in raw_docs]
        java_utils=DataPrepUtils()
        parsed_docs=java_utils.parseJavaClassesJython(raw_docs_objects)
        parsed_docs_strings=[gson.toJson(d) for d in parsed_docs]
        for doc in parsed_docs_strings:
                channel.send(doc)
        """)
        channel.send(raw_docs)
        parsed = [json.loads(item) for item in channel]
        group.terminate(timeout=1.0)
        time.sleep(1.0)
        return parsed

    def extract_corpora(self,
                        parsed_docs,
                        non_duplicates=None,
                        _filter=f'.+ {STRING_SEPARATOR} test \\d+$',
                        multipunct_threshold=5,
                        max_token_len=100):
        ''' Extract parallel corpus (source sequences paired with target sequences)
        Create mappings to track original test methods.
        Args:
            parsed_docs (list): list of dict object representing Java compilation units with parsed test cases
            non_duplicates: set of unique source sentences to control duplicates. Sentences already in the set will be skipped.
            _filter (str): regex pattern. Sequences matching the pattern will be excluded
        Returns:
            list: source sequences as list of strings
            list: target sequences as list of strings
            list: list of (doc_id, testcase_id) pairs for future tracking
        '''
        if not non_duplicates:
            non_duplicates = set()
        rejected_counts = {
            "src_seq_len": 0,
            'tgt_seq_len': 0,
            "token_len": 0,
            "parametrised_tc": 0,
            'meaningless_name': 0,
            'total': 0}
        string_stats = {
            "has_string": 0,
            "has_multitoken_string": 0,
            "has_punct_string": 0,
            'has_multipunct_string': 0,
            'all_strings': 0,
            "all_multitoken_strings": 0,
            "all_punct_strings": 0,
            'all_multipunct_strings': 0}
#         punct_stats={x:0 for x in string.punctuation}
        abstract_parent_count = 0

        init = [0] * len(string.punctuation)
        punct_stats = pd.DataFrame({'before': init,
                                    'after': init,
                                    'both': init,
                                    'none': init,
                                    'total': 0},
                                   index=[p for p in string.punctuation])

        if _filter:
            meaningless_pattern = re.compile(_filter)
        corpus_nl = []
        corpus_pl = []
        corpus_ids = []
        for doc in parsed_docs:
            try:
                for tc in doc["parsedTestCases"]:
                    rejected = False
                    try:
                        if not tc.get("body"):
                            continue

                        testAnnotationParams = tc.get("testAnnotation", "")
                        tgt_sequence = ' '.join(
                            [
                                "@Test",
                                tokenizer_plus.tokenize_sequence(
                                    testAnnotationParams,
                                    self.tokenization_params.split_identifiers,
                                    self.tokenization_params.split_strings,
                                    self.tokenization_params.exclude_list),
                                tokenizer_plus.tokenize_sequence(
                                    tc["body"],
                                    self.tokenization_params.split_identifiers,
                                    self.tokenization_params.split_strings,
                                    self.tokenization_params.exclude_list)]).replace(
                            "  ",
                            " ")
                        if tgt_sequence in non_duplicates:
                            continue

                        if tc.get("parameters"):
                            rejected_counts['parametrised_tc'] += 1
                            rejected = True

                        if (_filter and meaningless_pattern.match(
                                tc['title'])):
                            rejected_counts['meaningless_name'] += 1
                            rejected = True

                        if self.excesive_token_len(
                                tgt_sequence, max_token_len):
                            rejected_counts['token_len'] += 1
                            rejected = True

                        if self.out_of_bounds(
                                tgt_sequence,
                                self.size_bounds.tgtLower,
                                self.size_bounds.tgtUpper):
                            rejected_counts['tgt_seq_len'] += 1
                            rejected = True

                        class_name = self.remove_ending(
                            tc['classNameNL'], ['test', 'tests'])
                        if tc.get("ancestorClassNameNL", None):
                            ancestor_name = self.remove_ending(
                                tc['ancestorClassNameNL'], ['test', 'tests'])
                            class_name = " ".join([class_name, ancestor_name])

                        if tc["title"].startswith("test"):
                            tc["title"] = tc["title"][5:]

                        src_sequence = " ".join([class_name,
                                                 STRING_SEPARATOR, tc["title"]]).strip()
                        if self.out_of_bounds(
                                src_sequence,
                                self.size_bounds.srcLower,
                                self.size_bounds.srcUpper):
                            rejected_counts['src_seq_len'] += 1
                            rejected = True

                        if rejected:
                            rejected_counts['total'] += 1
                            continue

                        if 'ABSTRACT' in tc.get("classModifiers"):
                            abstract_parent_count += 1

                        corpus_nl.append(src_sequence + '\n')
                        corpus_pl.append(tgt_sequence + '\n')
                        corpus_ids.append(
                            "%s,%s,%s\n" %
                            (self.model_name, doc["_id"], tc["id"]))
                        non_duplicates.add(tgt_sequence)
                        if tc['containedStrings']:
                            tc_string_stats = get_string_stats(
                                tc['containedStrings'], punct_stats, multipunct_threshold)
                            for k in tc_string_stats:
                                string_stats[k] += tc_string_stats[k]
                    except Exception as e:
                        print(
                            "Exception on extracting corpora, test case %s " %
                            tc["body"], flush=True)
                        traceback.print_exc()
                        print(str(e))
                        print(self.model_name)
                        print('----------------------')
            except Exception as e:
                print(
                    "Exception on listing parsed tcs %s" %
                    str(e), flush=True)

        self.meta['rejected_counts'] = rejected_counts
        self.meta['abstract_parent_count'] = abstract_parent_count
        self.meta['string_stats'] = string_stats
        self.meta['punct_stats'] = punct_stats.T.to_dict()
        punct_stats.to_csv(self.dataset_loc + '/punct_stats.csv')
        punct_probs = punct_stats.iloc[:, 0:4].div(
            punct_stats.iloc[:, 4], axis=0)
        punct_probs.to_csv(self.dataset_loc + '/punct_probs.csv')
#         punct_probs.to_csv(self.dataset_loc + '/punct_probs_no_ind.csv', index=False)
        punct_probs.T.to_json(self.dataset_loc + '/punct_probs.json')
        return corpus_nl, corpus_pl, corpus_ids, non_duplicates

    def excesive_token_len(self, sequence, max_token_len):
        for token in sequence.split():
            if len(token) > max_token_len:
                print("Excessive token length")
                print(token)
                return True
        return False

    def out_of_bounds(self, sequence, lower, upper):
        '''Determine whether source and target sequences meet user-defined size bounds
        Returns:
            True if bounds exceeded, False otherwise.
        '''
        seq_len = len(sequence.split())
        return seq_len < lower or seq_len > upper

    def remove_ending(self, sequence, endings):
        for end in endings:
            if sequence.endswith(end):
                sequence = sequence[:-len(end)].strip()
                break
        return sequence

    def process_corpora(
            self,
            corpus_src,
            corpus_tgt,
            test_size=0.2,
            random_seed=None):
        ''' Divide source and target corpus into train and test set
        Extract vocabularies for source and target train sets
        Save the resulting 6 datasets.
        Args:
            corpus_src (list): list of strings representing source sequences
            corpus_tgt (list): list of strings representing target sequences
        '''

        if len(corpus_src) > 1:
            train_src, dev_src, train_tgt, dev_tgt = train_test_split(
                corpus_src, corpus_tgt, test_size=test_size, random_state=random_seed)
            self.save_dataset("dev", SRC, dev_src)
            self.save_dataset("dev", TGT, dev_tgt)
            self.meta['testset_size'] = len(dev_src)
        else:
            print("insufficient  data, creating train set only ", flush=True)
            train_src = corpus_src
            train_tgt = corpus_tgt
            self.meta['testset_size'] = 0

        self.save_dataset("train", SRC, train_src)
        self.save_dataset("train", TGT, train_tgt)
        self.create_vocab(train_src, SRC)
        self.create_vocab(train_tgt, TGT)

        self.meta["trainset_size"] = len(train_src)

    def create_vocab(self, dataset, suffix):
        ''' Create and save vocabulary (a list of unique words in a dataset, sorted by occurrence frequency
        Args:
            dataset (list): corpus to be processed as list of corpus sequences
            suffix: (str): suffix indicating dataset nature [src | tgt]
        '''
        SPECIAL_MARKERS = ['<unk>', '<s>', '</s>']
        content = " ".join(dataset).split()

        counts = collections.Counter(content)
        words_counts = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
        words, counts = list(zip(*words_counts))

        self.save_dataset(
            "vocab", suffix, [
                w + '\n' for w in SPECIAL_MARKERS + list(words)])
        self.save_dataset("vocab", suffix +
                          '.counts', ['0\n', '0\n', '0\n'] +
                          [str(c) +
                           '\n' for c in list(counts)])

        self.meta["vocab_%s_size" % suffix] = len(list(words))


def get_string_stats(string_list, punct_stats, multipunct_threshold=5):
    tc_stats = {
        'all_strings': 0,
        "all_multitoken_strings": 0,
        "all_punct_strings": 0,
        'all_multipunct_strings': 0}

    for s in string_list:
        for i in range(1, len(s) - 1):
            if s[i] in string.punctuation:
                c = [0] * 4
                c[0] = int(s[i - 1] == ' ')
                c[1] = int(s[i + 1] == ' ')
                c[2] = c[0] and c[1]
                c[3] = int(sum(c) == 0)

                punct_stats.loc[s[i], :] += c + [1]

        tc_stats['all_strings'] += 1
        token_list = tokenizer_plus.tokenize_sequence(
            s, False, True).split()[1:-1]
        if len(token_list) > 1:
            tc_stats['all_multitoken_strings'] += 1
        punct_tokens = [t for t in token_list if t in string.punctuation]
        if punct_tokens:
            tc_stats['all_punct_strings'] += 1
        if len(punct_tokens) > multipunct_threshold:
            tc_stats['all_multipunct_strings'] += 1

    tc_stats['has_string'] = 1 if tc_stats['all_strings'] else 0
    tc_stats['has_multitoken_string'] = 1 if tc_stats['all_multitoken_strings'] else 0
    tc_stats['has_punct_string'] = 1 if tc_stats['all_punct_strings'] else 0
    tc_stats['has_multipunct_string'] = 1 if tc_stats['all_multipunct_strings'] else 0

    return tc_stats


def get_string_stats_bak(string_list, punct_stats, multipunct_threshold=5):
    tc_stats = {
        'all_strings': 0,
        "all_multitoken_strings": 0,
        "all_punct_strings": 0,
        'all_multipunct_strings': 0}
    for s in string_list:
        tc_stats['all_strings'] += 1
        token_list = tokenizer_plus.tokenize_sequence(
            s, False, True).split()[1:-1]
        if len(token_list) > 1:
            tc_stats['all_multitoken_strings'] += 1
        punct_chars = [t for t in token_list if t in string.punctuation]
        if punct_chars:
            tc_stats['all_punct_strings'] += 1
        if len(punct_chars) > multipunct_threshold:
            tc_stats['all_multipunct_strings'] += 1
        for p in punct_chars:
            punct_stats[p] += 1

    tc_stats['has_string'] = 1 if tc_stats['all_strings'] else 0
    tc_stats['has_multitoken_string'] = 1 if tc_stats['all_multitoken_strings'] else 0
    tc_stats['has_punct_string'] = 1 if tc_stats['all_punct_strings'] else 0
    tc_stats['has_multipunct_string'] = 1 if tc_stats['all_multipunct_strings'] else 0

    return tc_stats
