'''
Created on Mar 18, 2020

@author: magda
'''

import re
import json
import sys
import os
import uuid
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


def clean_string(
        quotations,
        corpus_freqs,
        max_attempts=100,
        threshold_prob=0.2):
    all_punct = corpus_freqs.index.array
    esc = ['!', '"', '#', '\$', '%',
           '&', "'", '\(', '\)', '\*',
           '\+', ',', '-', '\.', '/', ':',
                ';', '<', '=', '>', '\?', '@', '\[', '\\', '\]',
                '\^', '_', '`',
                '{', '\|', '}', '~']
    escaped = dict(zip(all_punct, esc))
#     string_stats = [corpus_freqs.loc[corpus_freqs.index.intersection([ch for ch in string_token])] for string_token in quotations]
#     tc_puncts = [ [ (ch, string_token.index(ch) ) for ch in string_token if ch in all_punct ] for string_token in quotations ]
# string_stats = [corpus_freqs.loc[string_puncts,:] for string_puncts in
# [i[0] for i in tc_puncts if i] ]
    tc_puncts = [[ch for ch in string_token if ch in all_punct]
                 for string_token in quotations]
    string_stats = [corpus_freqs.loc[string_puncts, :].reset_index()
                    for string_puncts in tc_puncts]
    try:
        tc_stats = pd.concat(
            string_stats, keys=[
                i for i in range(
                    len(quotations))])
    except Exception as e:
        print(str(e))

    if tc_stats.empty:
        return [quotations]

    whisp_patterns = lambda x: {'none': f'{x}', 'before': f' {x}', 'after': f'{x} ', 'both': f' {x} '}

    hi_probs = tc_stats.iloc[:, 1:].idxmax(axis=1)
    for i in range(len(quotations)):
        for j in range(len(tc_puncts[i])):
            token = tc_puncts[i][j]
            state_name = hi_probs[i][j]
            try:
                quotations[i] = re.sub(
                    f'(\s?{escaped[token]}\s?)',
                    lambda x: whisp_patterns(token)[state_name],
                    quotations[i])
                state_id = list(tc_stats.columns).index(state_name)
                tc_stats.loc[i].iloc[j, state_id] = np.nan
            except Exception as e:
                print(str(e))
                break
    versions = [quotations]
#     mask = ''.join(random.choice(string.ascii_lowercase) for i in range(20))
# ref_ids = [ [ i for i in range(len(string_token)) if string_token[i] in
# sum(tc_puncts,[]) ] for string_token in quotations] #keep as a reference
    while max_attempts > 0 and tc_stats.iloc[:, 1:].sum().sum():
        option = random.choice(versions).copy()
#         (string_num,token) = tc_stats.max(axis=1).idxmax()
#         state_name = tc_stats.max().idxmax()
        highest_prob = tc_stats.iloc[:, 1:].max().max()

        locations = tc_stats[tc_stats.values ==
                             tc_stats.iloc[:, 1:].max().max()].index.tolist()
        states = tc_stats.columns[tc_stats.eq(
            tc_stats.iloc[:, 1:].max().max()).any()].tolist()

        locs = locations if highest_prob > threshold_prob else [
            random.choice(locations)]
        state = random.choice(states)

        for loc in locs:
            token = tc_stats.loc[loc]['index']

            string_id = loc[0]
            char_ids = [[i for i in range(
                len(string_token)) if string_token[i] in all_punct] for string_token in option]

            position = char_ids[string_id][loc[1]]
            replacement = whisp_patterns(token)[state]

            option[string_id] = replacement.join(
                [option[string_id][:position].strip(), option[string_id][position + 1:].strip()])
            tc_stats.loc[loc, state] = np.nan
        versions += [option]

#         hacked_option = re.sub(r'(\s?&\s?&\s?)', ' && ', option)
#         hacked_option = re.sub(r'(\s?=\s?>\s?)', ' => ', hacked_option)
#         if fixed_option not in versions:
#             versions +=[hacked_option]
        max_attempts -= 1

    return versions


def revert_whitespaces(line, corpus_freqs):
    #    qt_clean = [clean_string(x, corpus_freqs) for x in qt ]
    qt0 = re.findall(r'\s\"(.*?)\s\"\s', line)
    qt = re.findall(r'\s(\".*?\s\")\s', line)
    uids = [str(uuid.uuid4()) for x in qt]
    for i, j in zip(qt, uids):
        line = line.replace(i, j, 1)

    chars = re.findall(r'\s(\'.*?\s\')\s', line)
    chars_clean = [ch.replace("' ", "'").replace(" '", "'") for ch in chars]
    for i, j in zip(chars, chars_clean):
        line = line.replace(i, j, 1)

    if not qt:
        return [line]

    qt_clean = clean_string([x.strip() for x in qt0], corpus_freqs)

    line_options = []
    for string_option in qt_clean:
        line_option = line
        for i, j in zip(uids, string_option):
            #             j=f'"{j.strip()}"'
            j = f'"{j}"'
            line_option = line_option.replace(i, j, 1)
        line_options.append(line_option)

    return line_options


def write_input_for_java_formatter(
        reconstructed,
        project_mappings_dir,
        input_dir):
    os.makedirs(input_dir, exist_ok=True)
    with open(project_mappings_dir) as f:
        mappings = json.load(f)

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
    unspaced_file = f'{cfg.reverted_dir}/unspaced_dev.pl'

    os.mkdir(cfg.reverted_dir)
    os.mkdir(cfg.formatted_dir)

    with open(f'{cfg.formatted_dir}/meta.txt', 'w') as f:
        f.writelines([f'{f}\n' for f in [cfg.generated_file,
                                         unsplit_file,
                                         unspaced_file,
                                         cfg.project_mappings_dir,
                                         cfg.formatted_dir,
                                         cfg.stats_file]])

    corpus_freqs = pd.read_csv(cfg.stats_file, index_col=0)

    with open(cfg.generated_file) as f:
        generated = f.readlines()

    unsplit = [revert_split(x) for x in generated]
    if unsplit_file:
        with open(unsplit_file, 'w') as f:
            f.writelines([f'{x}' for x in unsplit])

    unspaced = [revert_whitespaces(x, corpus_freqs) for x in unsplit]
    if(unspaced_file):
        with open(f'{unspaced_file}.json', 'w') as f:
            json.dump(unspaced, f, indent=2)
        with open(unspaced_file, 'w') as f:
            f.writelines([f'{x}\n' for x in unspaced])

    if cfg.project_mappings_dir and cfg.formatted_dir:
        write_input_for_java_formatter(
			unspaced, cfg.project_mappings_dir, f'{cfg.formatted_dir}/in')

    run_java_formatter(f'{cfg.formatted_dir}/in', f'{cfg.formatted_dir}/out', cfg.lib_path)


if __name__ == '__main__':
    main()
