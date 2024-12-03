# ExTra

Pre-requisites:
* python >= 3.11
* java >= 17
* maven >= 3.9.6
* jython 2.7.2 (optional)


## Getting started:
```
git clone git@github.com:magdakacmajor/extra.git
cd extra/extra_java
mvn install
cd ../extra_python
pip install -r extra/extra_python/requirements.txt
cd src
```

## Creating dataset

The code for collecting and processing a dataset for code creation is implememented mainly in Python, but parsing the collected code is implemented in Java. All code can be run with a single command using Jython (Option 1 below). Users who cannot or do not want to install Jython, can execute Python and Java modules separately (Option 2). 

Regardless the selected option, update the following properties in the `config/preprocessing_params.json`:
- `repository_dir: str` the path to the root directory containing one or more source code repositories/projects. Example: "/home/username/git".
- `target_repos: str` comma-separated list of repositories/projects (located in the `repository_dir`) to be parsed. Example: "spring-framework".
- `dataset_loc: str` output location. Example: "/home/username/my_new_dataset".
- `label: str` (optional) user-defined name of the dataset (default is the name of the repository/project from which the dataset was extracted).
- `size_bounds: list` lower and upper bounds of the source and target sequence lenghts, in the following order: [<MIN_SRC_LEN>, <MAX_SRC_LEN>, <MIN_TGT_LEN>, <MAX_TGT_LEN>]). Example: [5,150,5,150]. This example value will produce a dataset where the minimum lengths of source and target sequences are 5 tokens, and the maximum lengths of source and target sequences is 150 tokens.
- `test_size: float` the size of the test set with respect to the full corpus. Example: 0.2. This example value will result in splitting the corpus into train set and test set at the ratio of 0.8 : 0.2.
- `random_seed: int` (optional) random seed to be used for the trainset/testset split.
- `_filter: str` (optional) regular expression pattern to be used for filtering the output. Example: "test\\d+$". This example value will result in rejecting test cases with meaningless method names, such as "test1", "test3" etc.

### Option 1 (Jython required) 
Update `extra_python/config/config.txt`:
- set `classpath=<EXTRA_HOME>/extra_java/javalib/*:<EXTRA_HOME>/extra_java/target/classes`
- set `jython_path=<JYTHON_HOME>`

Execute:

```
cd <EXTRA_HOME>/extra_python/src
export PYTHONPATH=$PYTHONPATH:$(pwd)
python preprocessing/multi_repos.py
```

### Option 2 
1. Run Python module
* Update `extra_python/config/config.txt`
    * set `parsed`: `false`

* Execute:
```
cd <EXTRA_HOME/extra_python>
export PYTHONPATH=$PYTHONPATH:$(pwd)
python preprocessing/multi_repos_no_jython.py
```
2. Run Java module
* Execute:

```
cd <EXTRA_HOME>/extra_java/src
export CLASSPATH=<EXTRA_HOME>/bin:<EXTRA_HOME>/bin/javalib/* 
java preprocessing.Driver parse <DATASET_LOC>/parsed_data
```

3. Re-run Python module with updated configuration:
* Update `extra_python/config/config.txt`:
    * set `parsed`: `true`
* Execute:
```
cd <EXTRA_HOME/extra_python>
export PYTHONPATH=$PYTHONPATH:$(pwd)
python preprocessing/multi_repos_no_jython.py
```

### Expected output:
The directory specified as the `dataset_loc` property is populated with subdirectories, one for each repository/project listed under `target_repos`. 
Each subdirectory contains the following folders: 
- `parsed_data` - the directory containing parsed test cases extracted from the repository;
- `corpora` - the directory containing parallel corpora divided to training and test sets and vocabulary files;
- `meta.json` - the file containing metadata. 
- `punct_probs.csv`, `punct_probs.json`, `punct_stats.csv` - stat files for handling the formatting of embedded strings (used by postprocessing scripts)/

## ExTra

### Creating metadata file
This Python module generates the metadata file needed for the execution of the ground-truth and the generated code.

1. Update `extra_python/mapping_params.json`.
- `dataset_loc: str` the path to the directory containing parsed methods and extracted corpora. Example: "/home/username/my_new_dataset".
- `label: str` the name of the dataset. Example: "spring-framework".
- `output_file: str` the path to and the name of the file to store the output. Example: "/home/username/myworkspace/mappings.json".
- `target_file: str` the dataset (train set or test set) to be mapped. In a typical scenario it will always be the code part of the test set. Example: "test.pl".

2. Execute:
```
cd <EXTRA_HOME/extra_python>
export PYTHONPATH=$PYTHONPATH:$(pwd)
python extra/create_project_mappings.py
```

#### Expected output
The file specified in the `output_file` property contains metadata for all the entries in the corpus specified under the `target_file`.

### Postprocessing
This Python module handles outputs of models that generate tokenized code (removes tokenization and formats the generated methods to enable compilation.

1. Update `extra_python/postprocessing_params.json`.
- `generated_file: str` full path to generated file. Example: "/home/username/myworkspace/generated.pl".
- `project_mapping: str` full path to the metadata file created in the previous step. Example: "/home/username/myworkspace/mappings.json".
- `reverted_dir: str` the path to the directory to store partially processed files (after reverting tokenization only). Useful for debugging purposes. Example: "/home/username/myworkspace/reverted".
- `formatted_dir: str` the path to the directory to store final outputs (formatted files ready to be inserted to the original source code files in the repository). Example: "/home/username/myworkspace/formatted".
- `stats_file: str` the path to the stats file created during dataset creation. Example: "/home/username/my_new_dataset/punct_probs.csv".
- `lib_path: str` the path to the [google-java-format](https://github.com/google/google-java-format) jar file (provided in this repository in `extra_python/extra/lib` directory). Example: "lib/google-java-format-1.7-all-deps.jar"

2. Execute:
```
cd <EXTRA_HOME/extra_python>
export PYTHONPATH=$PYTHONPATH:$(pwd)
python extra/reverse_preprocessing.py
```

#### Expected output
The directory specified in the `formatted_dir` property is populated with files containing generated methods, de-tokenized and properly formatted.


### Code execution and collecting execution traces
This tool is implemented in Java, and leverages [JavaParser](https://javaparser.org/) library to extract the original ground-truth methods from the parent classes and substitute them with generated methods formatted with the google-java-format library. Each substituted method is executed individually and the execution traces are collected and stored in the user-specified directory. The module needs to be run twice: (1) to execute the generated methods (`replaceMethod` property set to `true`), and (2) to execute ground-truth methods (`replaceMethod` property set to `false`).

The ExTra code requires JDK 21 or later. If the project containing the generated code requires an earlier version of Java, then that earlier version should be specified as an environmental variable, and the ExTra code should be run using Java 21 (or later)

1. Update `extra_java/config/report_properties`
- `project_path: str` the path to the repository containing the target source code. Example: "/home/username/git/spring-framework".
- `workingDir: str` root directory for storing ExTra outputs. Example: "/home/username/myworkspace". 
- `has_subprojects: bool` whether the target git repository contains subprojects.
- `profile: str` (if applicable) Maven profile name of the target project. 
- `skipPaths: str` (optional) comma-separated list of subdirectories in the target repository that should be skipped during the execution.
- `mapping_file: str` the name of the metadata file (should be located in the `workingDir`). Example: "mapping.json".
- `substitution_dir: str` the directory containing files with formatted generated code to be inserted into the parent classes. Example: "/home/username/myworkspace/formatted". For ground-truth code execution, this property should be left empty.
- `standardLength: int` the maximum lengths (measured as the number of lines) of the ground-truth or generated code. 
- `outDir: str` the name of the directory to store the collected execution traces. This directory will be created within the `workingDir`. Example "trace_reports_generated".
- `jarClassesPath: str` the path to the directory containing the dependency libraries of the target project. Example: "/home/username/.gradle/caches/modules-2/files-2.1".
- `modules: str` comma-separated list of modules to be searched for Jacoco binary files produced after the execution of ground-truth or generated methods.
- `replaceMethod: bool` true for the execution of generated code, false for the ground-truth code execution. 

2. Execute:
```
cd <EXTRA_HOME>/extra_java
export JAVA_HOME=<LOCATION OF JAVA REQUIRED BY THE TARGET PROJECT>
export CLASSPATH=<EXTRA_HOME>/extra_java/javalib/*:<EXTRA_HOME/extra_java/lib811/*:EXTRA_HOME/extra_java/bin
<JAVA 21 DIR>/java extra.SubstituteMethods <PATH TO THE MAPPING FILE>
<JAVA 21 DIR>/java extra.DetailedReports config/report.properties >> <LOG DIRECTORY>/extra.log
```

#### Expected output
For each executed method, the directory specified in the `outDir` property contains a subdirectory populated with files containing execution logs from all visited methods.

### Converting exectution logs to vectors and calculating ExTra score

1. Update `extra_python/config/eval_config.json' file:

- `mappings_path: str` the path to the metadata file. Example: "/home/username/myworkspace/mapping.json".
- `gt_path: str` the path to the directory containing execution traces of the ground-truth code. Example: "/home/username/myworkspace/trace_reports_gt/logs0".
- `gen_path: str` the path to the directory containing execution traces of the generated code. Example: "/home/username/myworkspace/trace_reports_generated/logs0".
- `log_path: str` the path to the log file from the execution. Example: "/home/username/workspace/trace_reports_generated/extra.log".
- `out_path: str` the path to the pickle file to store the processed vectors and the sentence level scores of ExTra and three source-code based metrics.
- `dev_pl: str` the path to the ground-truth code.
- `generated_dev_pl: str` the path to the generated code.
- `lang: str` programming language of the generated code. Example: "java". 
- `revert_sem_split: str` 
- `include_notcompiled: str` 

2. Execute:
```
cd <EXTRA_HOME/extra_python>
export PYTHONPATH=$PYTHONPATH:$(pwd)
python extra/evaluation.py config/eval_config.json
```
#### Expected output
The directory specified in `out_path` property is populated with a pickle containing serialized DataFrames with ground-truth and generated vectors, and the sentence-level ExTra scores, along with the sentence-level scores of three source-code based metrics (BLEU, Levenshtein ratio and CodeBLEU).