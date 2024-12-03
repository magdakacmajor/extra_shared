
import sys
import os
import shutil
import uuid
import json
from preprocessing.preprocessor import SRC, TGT
from types import SimpleNamespace
from preprocessing.local_preprocessor import LocalPreprocessor
from config.custom_configparser import CustomConfigParser


def main():
    nojunit = []
    path = f'{os.path.abspath(os.path.dirname(__file__))}/../config/preprocessing_params.json' if len(
        sys.argv) == 1 else sys.argv[1]
    with open(path) as f:
        params = json.load(f)
    cfg = SimpleNamespace(**params)

    tkn_params = CustomConfigParser().get_tokenization_params()
    params = params | tkn_params

    for k, v in params.items():
        print(k, v)

    try:
        with open(cfg.non_duplicates, encoding='utf-8') as repository:
            nd = [x.strip() for x in repository.readlines()]
            non_duplicates = set(nd)
    except BaseException:
        non_duplicates = set()

    total_rejected_counts = {k: 0 for k in ['src_seq_len',
                                            'tgt_seq_len',
                                            'token_len',
                                            'parametrised_tc',
                                            'meaningless_name',
                                            'total']}
    total_abstract_parents = 0
    total_string_stats = {k: 0 for k in ['has_string',
                                         'has_multitoken_string',
                                         'has_punct_string',
                                         'has_multipunct_string',
                                         'all_strings',
                                         'all_multitoken_strings',
                                         'all_punct_strings',
                                         'all_multipunct_strings']}

    os.makedirs(os.path.join(cfg.dataset_loc, "corpora"), exist_ok=True)
    repository_list = cfg.target_repos.split(',') if cfg.target_repos else next(os.walk(cfg.repository_dir))[1]
    for repository in repository_list:
        print("start processing %s..." % repository)
        prep = LocalPreprocessor(
            os.path.join(
                cfg.repository_dir,
                repository),
            cfg.dataset_loc,
            cfg.label if cfg.label else repository,
            size_bounds=cfg.size_bounds,
            origin_url="https://github.com/%s" %
            repository.replace(
                '_',
                '/'))
        
        if not cfg.parsed:
            try:
                raw_docs = prep.crawl_repository()
                prep.create_dataset_dir()
                for doc in raw_docs:
                    prep.save_doc(doc)
                    
            except Exception as e:
                print("Error on crawling %s" % repository)
                print(str(e))

        if cfg.parsed:
            try:
                parsed_docs = prep.get_parsed_data()
                
                (corpus_src,
                 corpus_tgt,
                 corpus_ids,
                 non_duplicates) = prep.extract_corpora(parsed_docs,
                                                    non_duplicates=non_duplicates,
                                                    _filter=cfg._filter,
                                                    multipunct_threshold=cfg.multipunct_threshold)
            except Exception as e:
                print("Error on parsing %s" % repository)
                print(str(e))
                
            if len(corpus_src) > 0:
                prep.save_dataset("corpus", SRC, corpus_src)
                prep.save_dataset("corpus", TGT, corpus_tgt)
                prep.save_dataset("corpus", "ids", corpus_ids)
                prep.process_corpora(
                    corpus_src,
                    corpus_tgt,
                    test_size=cfg.test_size,
                    random_seed=cfg.random_seed)
            else:
                print("Extracted corpus is empty", flush=True)

            prep.meta["parsed_size"] = len(parsed_docs)
            prep.meta["corpus_size"] = len(corpus_src)
            prep.meta['random_seed'] = cfg.random_seed
            prep.meta['test_size'] = cfg.test_size
            prep.meta['multipunct_threshold'] = cfg.multipunct_threshold
            prep.save_meta()
            
            info=prep.meta
            if info["parsed_size"] > 0 and info["corpus_size"] > 0:
                print("OK: %s" % info["name"])
                print("non duplicates: %i" % len(non_duplicates))
                rejected_counts = info['rejected_counts']
                for k in rejected_counts.keys():
                    total_rejected_counts[k] += rejected_counts[k]
                total_abstract_parents += info['abstract_parent_count']
                string_stats = info['string_stats']
                for k in string_stats:
                    total_string_stats[k] += string_stats[k]

            else:
                nojunit.append(info["name"] + "\n")
                print("Nojunit: %s" % info["name"])
                if info['parsed_size'] > 0:
                    shutil.rmtree(os.path.join(cfg.dataset_loc, repository))

            with open(os.path.join(cfg.dataset_loc, "corpora", "nojunit.ts"), 'w', encoding='utf-8') as repository:
                repository.writelines(nojunit)
            print("non duplicates: %i" % len(non_duplicates))
        
            params["uuid"] = str(uuid.uuid4())
            params['total_rejected'] = total_rejected_counts
            params['total_abstract_parents'] = total_abstract_parents
        
            with open(os.path.join(cfg.dataset_loc, "corpora", "meta.json"), "w", encoding='utf-8') as m:
                json.dump(params, m, indent=3, sort_keys=True)


if __name__ == '__main__':
    main()
