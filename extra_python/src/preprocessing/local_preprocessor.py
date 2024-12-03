import os
import json
from preprocessing.preprocessor import Preprocessor, overrides


class LocalPreprocessor(Preprocessor):
    """Implements preprocessor with local storage option
    """

    def __init__(self, repository,
                 dataset_loc,
                 model_name="",
                 size_bounds=[5, 300, 5, 300],
                 origin_url=None):

        self.storage_dir = os.path.join(dataset_loc, model_name)
        self.parsed_data_dir = os.path.join(os.path.join(
            self.storage_dir, model_name), "parsed_data")
        self.corpus_dir = os.path.join(self.storage_dir, "corpora")

        super(LocalPreprocessor, self).__init__(repository=repository,
                                                dataset_loc=dataset_loc,
                                                model_name=model_name,
                                                size_bounds=size_bounds,
                                                origin_url=origin_url)

    @overrides(Preprocessor)
    def create_dataset_dir(self):
        if not os.path.exists(self.parsed_data_dir):
            os.makedirs(self.corpus_dir)
            os.makedirs(self.parsed_data_dir)
        else:
            raise Exception("Model name already taken. Choose a unique name.")

    @overrides(Preprocessor)
    def save_meta(self):
        with open(os.path.join(self.storage_dir, "meta.json"), 'w', encoding='utf-8') as f:
            json.dump(self.meta, f, indent=3, sort_keys=True)

    @overrides(Preprocessor)
    def save_doc(self, doc):
        doc_path = os.path.join(self.parsed_data_dir, doc['_id'])
        with open(doc_path, 'w') as out:
            json.dump(doc, out)

    @overrides(Preprocessor)
    def save_dataset(self, filename, suffix, dataset):
        with open(os.path.join(self.corpus_dir, "%s.%s" % (filename, suffix)), "w", errors="ignore") as f:
            f.writelines(dataset)
    
    @overrides(Preprocessor)    
    def get_parsed_data(self):
        parsed_data=[]
        for f in os.listdir(self.parsed_data_dir):
            parsed_data.append(json.load(open(f'{self.parsed_data_dir}/{f}')))
        return parsed_data
