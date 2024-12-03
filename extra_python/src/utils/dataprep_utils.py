'''
Created on 25 Sep 2017

@author: magdalena.kacmajor@ie.ibm.com
'''
import collections
import re
import os
import fnmatch
import json
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

SPECIAL_MARKERS = ['<unk>', '<s>', '</s>']

_NL = '.nl'
_PL = '.pl'
CORPUS = 'corpus'
VOCAB = 'vocab'
TRAIN = 'train'
DEV = 'dev'
TEST = 'test'


def savelines(dirname, filename, suffix, lines):
    with open(os.path.join(dirname, filename + suffix), mode="w", encoding='utf-8') as f:
        for l in lines:
            f.write(str(l) + ('' if str(l).endswith('\n') else '\n'))


def split_datasets(data_dir):
    with open(os.path.join(data_dir, CORPUS + _NL), encoding='utf-8') as f:
        corpus_nl = f.readlines()
    with open(os.path.join(data_dir, CORPUS + _PL), encoding='utf-8') as f:
        corpus_pl = f.readlines()

#     for index, seq in enumerate(corpus_pl):
#         seq = re.sub('([().;,={}""<>+:\\-\[\]/])', r' \1 ', seq)
#         seq = re.sub('\s{2,}', ' ', seq)
#         corpus_pl[index] = seq

    train_nl, dev_nl, train_pl, dev_pl = train_test_split(
        corpus_nl, corpus_pl, test_size=0.2)
#    dev_nl, test_nl, dev_pl, test_pl = train_test_split(dev_nl, dev_pl, test_size = 0.5)
    test_nl = dev_nl
    test_pl = dev_pl

    savelines(data_dir, TRAIN, _NL, train_nl)
    savelines(data_dir, TRAIN, _PL, train_pl)

    savelines(data_dir, DEV, _NL, dev_nl)
    savelines(data_dir, DEV, _PL, dev_pl)

    savelines(data_dir, TEST, _NL, test_nl)
    savelines(data_dir, TEST, _PL, test_pl)


def parse_pl(content):
    content_split = []
    for c in content:
        c = re.split('(\W)', c)
        c = list(filter(None, c))  # remove empty strings
        content_split = content_split + c

    return content_split


def create_vocab(data_dir, _suffix):
    with open(os.path.join(data_dir, TRAIN + _suffix), "r") as f:
        content = f.read().replace("\n", " ").split()

#     if _suffix == _PL:
#         content = parse_pl(content)

    counts = collections.Counter(content)
    words_counts = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    words, counts = list(zip(*words_counts))

    savelines(data_dir, VOCAB, _suffix, SPECIAL_MARKERS + list(words))
    savelines(data_dir, VOCAB, _suffix + '.counts', [0, 0, 0] + list(counts))


''''
Find all classes containing methods with @Test annotation:
input: directory to search
output: an array of paths to identied methods
'''''


def find_test_classes(src_dir):
    test_classes = []
    for root, _, files in os.walk(os.path.abspath(src_dir)):
        for fname in fnmatch.filter(files, '*.java'):
            fpath = os.path.join(root, fname)
            with open(fpath, encoding='utf-8', errors='ignore') as f:
                try:
                    if '@Test' in f.read().split():
                        test_classes.append(fpath)
                except UnicodeDecodeError as e:
                    print("%s : %s" % (e, fpath))
    return test_classes


def find(filename, path):
    for root, _, files in os.walk(path):
        if filename in files:
            return os.path.join(root, filename)
    return None


def excluded(exclude_dir, include_val, hj):
    for ed in exclude_dir:
        if ed in hj['fpath']:
            return True
    for key in include_val.keys():
        if include_val[key] != hj[key]:
            return True

    return False


def find_all_files(filename, path, exclude_dir=[], include_val={}):
    hjsons = []
    for root, _, files in os.walk(path):
        if filename in files:
            fpath = os.path.join(root, filename)
            with open(fpath, 'r', encoding='utf-8') as f:
                hj = json.load(f)
                hj['fpath'] = fpath
                if not excluded(exclude_dir, include_val, hj):
                    hjsons.append(hj)
    return hjsons


def find_tests_and_testees(src_dir):
    tests = []
    testees = []
    for root, _, files in os.walk(os.path.abspath(src_dir)):
        for test in fnmatch.filter(files, '*Tests.java'):
            candidate = test.replace('Tests', '')
            testee = find(candidate, src_dir)
            if(testee):
                testees.append(testee)
                tests.append(os.path.join(root, test))
    return tests, testees


def save_as_jsons(pathlist, dest_dir, overwrite=False):
    count = 0
    for path in pathlist:
        doc = {}
        count += 1
        with open(path, encoding='utf-8') as f:
            rawClass = {}
            rawClass[path.split('/')[-1]] = f.read()
            doc['rawClasses'] = [rawClass]
            if overwrite:
                doc['_id'] = '%s' % (path.split('/')[-1])
            else:
                doc['_id'] = '%s-%i' % (path.split('/')[-1], count)
        doc_path = os.path.join(dest_dir, doc['_id'])

        if os.path.exists(doc_path):
            print('%s already exists' % doc_path)

        with open(doc_path, 'w', encoding='utf-8') as out:
            json.dump(doc, out)


def get_lengths_estimation(filename, block=100, outdir=None):
    with open(filename, encoding='utf-8') as f:
        lines = f.readlines()
    lens = [len(x.rstrip().split()) for x in lines]
    counts = collections.Counter(lens)
    len_counts = sorted(
        counts.items(), key=lambda x: (-x[0], x[1]), reverse=True)

    df = pd.DataFrame.from_records(len_counts, columns=["blocks", "counts"])

    blocks = df.groupby(pd.cut(df["blocks"], np.arange(
        len_counts[-1][0] + block, step=block))).sum()
    if outdir is None:
        outdir = os.path.join(
            ('/').join(filename.split('/')[0:-1]), 'len_stats/')
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    with open(os.path.join(outdir, "%s-block-%i.csv" % (filename.split('/')[-1], block)), 'w') as out:
        blocks.to_csv(out, columns=["counts"])


def filter_corpora(data_dir, low, high):
    corpusnl = os.path.join(data_dir, CORPUS + _NL)
    corpuspl = os.path.join(data_dir, CORPUS + _PL)
    with open(corpusnl, 'r', encoding='utf-8') as nl, open(corpuspl, 'r', encoding='utf-8') as pl:
        nl, pl = zip(*((nl, pl) for nl, pl in zip(nl, pl)
                     if low < len(pl) / len(nl) < high))

    filtereddir = os.path.join(data_dir, "balanced_%1.1f_%1.1f") % (low, high)
    os.mkdir(filtereddir)
    savelines(filtereddir, CORPUS, _NL, nl)
    savelines(filtereddir, CORPUS, _PL, pl)


def merge_corpora(file1, file2):
    with open(file1, encoding='utf-8') as f1, open(file2, encoding='utf-8') as f2:
        merged = f1.readlines() + f2.readlines()
    return merged
