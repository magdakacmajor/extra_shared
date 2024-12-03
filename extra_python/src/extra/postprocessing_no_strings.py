'''
Created on Mar 18, 2020

@author: magda
'''

import re
import json
import sys
import os
import uuid
import string
import subprocess
import shlex
import pandas as pd
import numpy as np
import random
from types import SimpleNamespace


def revert_split(code):
    annotated = re.findall('».*?«', code)
    cleaned = re.findall('»(.*?)«', code)
    cleaned = [i.replace(' ', '') for i in cleaned]
    for i, j in zip(annotated, cleaned):
        try:
            code = code.replace(i, j, 1)
        except Exception as e:
            print(str(e))
            print(code)
    return code

def fix_strings(line, contained_strings):
    qt = re.findall(r'\s(\".*?\s\")\s', line)
    for i,j in zip(qt, contained_strings[:len(qt)]):
        line=line.replace(i, j, 1)
    return [line]


def write_input_for_java_formatter(reconstructed,
                                    mappings,
                                    input_dir):
    os.makedirs(input_dir, exist_ok=True)

    for i in range(0, len(mappings)):
        pm = mappings[i]
        if not pm['executable']:
            print(f'{i}: {pm["className"]}.{pm["methodName"]}')
            continue
        exceptions = f'throws {pm["thrownExceptions"].strip().replace(" ", ",")}' if pm['thrownExceptions'] else ''
        modifiers = f'{pm["modifiers"].lower()} ' if pm['modifiers'] else ''
        for j in range(0, len(reconstructed[i])):
            try:
                with open(f'{input_dir}/{i}_{j}.java', 'w') as f:
                    (annotation, body) = reconstructed[i][j].split('{', 1)
                    f.write(
                        f'class {pm["className"]} {{ {annotation}{modifiers}void {pm["methodName"]}() {exceptions}{{{body} }}')
            except:
                print(f'{i}_{j} {pm["className"]} {pm["methodName"]}')


def run_java_formatter(input_dir, output_dir, jar_path):
    os.makedirs(output_dir, exist_ok=True)
    count_failed = 0
    count_done = 0
    for fname in os.listdir(input_dir):
        process = subprocess.Popen(
            shlex.split(f'java -jar {jar_path} {input_dir}/{fname}'),
            stdout=subprocess.PIPE)
        output = process.communicate()
        if len(output[0]) > 0 and not output[1]:
            with open(f'{output_dir}/{fname}', 'w') as f:
                f.write(output[0].decode('utf-8'))
            count_done += 1
        else:
            print(fname)
            count_failed += 1
    print(f'Failed: {count_failed}')


def main():
    path = f'{os.path.abspath(os.path.dirname(__file__))}/../config/postprocessing_params.json' if len(
	    sys.argv) == 1 else sys.argv[1]
    with open(path) as f:
        params = json.load(f)
    cfg = SimpleNamespace(**params)

    unsplit_file = f'{cfg.reverted_dir}/unsplit_dev.pl'
    fixedstr_file = f'{cfg.reverted_dir}/fixedstr_dev.pl'

    os.mkdir(cfg.reverted_dir)
    os.mkdir(cfg.formatted_dir)

    with open(f'{cfg.formatted_dir}/meta.txt', 'w') as f:
        f.writelines([f'{f}\n' for f in [cfg.generated_file,
                                         unsplit_file,
                                         fixedstr_file,
                                         cfg.project_mappings_dir,
                                         cfg.formatted_dir
                                         ]])

    with open(cfg.generated_file) as f:
        generated = f.readlines()

    unsplit = [revert_split(x) for x in generated] if cfg.split else generated
    with open(unsplit_file, 'w') as f:
        f.writelines([f'{x}' for x in unsplit])
            
    with open(cfg.project_mappings_dir) as f:
        mappings = json.load(f)

    fixedstr = [fix_strings(unsplit[m['idx']], m['containedStrings']) for m in mappings]
    with open(fixedstr_file, 'w') as f:
        f.writelines([f'{x}\n' for x in fixedstr])

    write_input_for_java_formatter(
			fixedstr, cfg.project_mappings_dir, f'{cfg.formatted_dir}/in')

    run_java_formatter(f'{cfg.formatted_dir}/in', f'{cfg.formatted_dir}/out', cfg.lib_path)


if __name__ == '__main__':
    main()
