import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import os, sys, json, pickle
import re
import subprocess, shlex
import pandas as pd
import numpy as np
import nltk
from tempfile import mkstemp
from io import StringIO
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.metrics.pairwise import cosine_similarity
from extra.levenstein_plus import levenshtein, generated
from types import SimpleNamespace

from CodeBLEU import bleu as cb_bleu
from CodeBLEU import weighted_ngram_match
from CodeBLEU import syntax_match
from CodeBLEU import dataflow_match

import codebleu
import Levenshtein as Leven

pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)

excluded=[
	# 'ConcurrentReferenceHashMap',
	# 'org.apache.commons'
		 ]

cb_path=f'{os.path.abspath(os.path.dirname(__file__))}/../CodeBLEU'

def get_reverse_map(path):
	with open(path) as f:
		data = json.load(f)
	revmap={}
	reverse_map = {data[i]["testcase_fullname"] : i for i in range(len(data))}
	for i in range(len(data)):
		revmap[data[i]["testcase_fullname"]]=i
		
	return data, revmap

def _filter(cut_name, excluded):
	for pattern in excluded:
		if pattern in cut_name:
			return True
	return False

def get_cut_traces(path, status='status'):
	cut=pd.read_csv(path)
	empty_lines=cut[cut[status]==0]
	cut=cut[cut[status] > 0 ]
	cut.loc[cut[status] == 1, status] = 0
	cut.loc[cut[status] > 1, status] = 1 #ignore difference between 'covered' and 'partially covered'
	return cut, empty_lines

def compare_traces(gt_path, gen_path, tc_fullname, excluded, subdir='combo', status='status'):
	gt_files = os.listdir(f'{gt_path}/{tc_fullname}/{subdir}')
	try:
		gen_files = os.listdir(f'{gen_path}/{tc_fullname}/{subdir}')
	except FileNotFoundError as e:
#		 print(str(e))
		gen_files=[]

	[tc_class, tc_method]=tc_fullname.rsplit('.', 1)
	
	def ignore_substituted(df, tc_method):
		df = df[~(df.method.isin([tc_method, '<init>', '<clinit>']))]
		df = df[~(df.method.str.contains(f'lambda\${tc_method}\$'))]
		return df
	
	gt_logs, gen_logs=[],[]
	for cut_name in gt_files:
		if _filter(cut_name, excluded):
			continue
		
		(gt, _)=get_cut_traces(f'{gt_path}/{tc_fullname}/{subdir}/{cut_name}')
		if cut_name in gen_files:
			(gen, _)=get_cut_traces(f'{gen_path}/{tc_fullname}/{subdir}/{cut_name}')
		else:
			gen = pd.DataFrame(columns=gt.columns)
		if tc_class in cut_name.replace('_','.'):
			gt = ignore_substituted(gt, tc_method)
			gen = ignore_substituted(gen, tc_method)
		tmp=pd.merge(gt, gen, how='outer', on=['cut','method', 'desc', 'line'])
#		 if not tmp[tmp.duplicated('line', keep=False)].empty:
#			 print(cut_name)
#		 if tmp.isnull().values.any():
#			 print(cut_name)				s
		tmp['status_x'].fillna(0, inplace=True)
		tmp['status_y'].fillna(0, inplace=True)
		tmp['status_y'] = tmp['status_y'].astype(int)
		gt_logs.append( tmp[['cut', 'method', 'desc', 'line', 'status_x']].rename(columns={'status_x':'status'}) )
		gen_logs.append( tmp[['cut', 'method', 'desc','line', 'status_y']].rename(columns={'status_y':'status'}) )
#		 if not gt.reset_index(drop=True).equals(gt_logs[-1]) or not gen.reset_index(drop=True).equals(gen_logs[-1]):
#			 print(cut_name)

		assert(np.array_equal(gt_logs[-1][['cut', 'method', 'desc', 'line']].values, gen_logs[-1][['cut','method', 'desc', 'line']].values) )
		
	for cut_name in set(gen_files) - set(gt_files):
		if _filter(cut_name, excluded):
			continue
		(gen, _)=get_cut_traces(f'{gen_path}/{tc_fullname}/{subdir}/{cut_name}')
		gen_logs.append(gen)
		gt=gen.copy()
		gt[status]=0
		gt_logs.append(gt)
		assert(np.array_equal(gt[['cut', 'method', 'desc', 'line']].values, gen[['cut', 'method', 'desc', 'line']].values))
	try:
		gt_testcase=pd.concat(gt_logs, ignore_index=True)
	except:
		print('akuku')
	gt_testcase[status]=gt_testcase[status].astype('int64')
	gen_testcase=pd.concat(gen_logs, ignore_index=True)
	gen_testcase[status]=gen_testcase[status].astype('int64')
	try:
		assert( np.array_equal(gt_testcase[['cut','method', 'desc', 'line']].values, gen_testcase[['cut','method', 'desc', 'line']].values) )
	except Exception as e:
		print('akuku')
		
	return gt_testcase, gen_testcase

def read_and_format (tc_path, lib_path) :
	process = subprocess.Popen(shlex.split(f'java -jar {lib_path} {tc_path}'), stdout=subprocess.PIPE)
	output = process.communicate()
	if len(output[0]) > 0 and not output[1]:
		formatted = output[0].decode('utf-8')
	else:
		formatted = None
	return formatted	

def get_formatted_body(tc, lib_path):	
	exceptions = f'throws {tc["thrownExceptions"].strip().replace(" ", ",")}' if tc['thrownExceptions'] else ''
	modifiers = f'{tc["modifiers"].lower()} ' if tc['modifiers'] else ''

	fd, path = mkstemp(suffix='.java')
	with os.fdopen(fd, 'w') as f:
		f.write(f'class {tc["className"]} {{ @Test {modifiers}void {tc["methodName"]}() {exceptions}{tc["body"]} }}')
		
	formatted_body = read_and_format(path, lib_path)
	os.unlink(path)
	return formatted_body
	
def compare_source_code(tc_or_path, gen_path, lib_path):
	if not os.path.exists(gen_path):
		return np.nan, np.nan
	
	if isinstance(tc_or_path, dict):
		formatted_gt=get_formatted_body(tc_or_path, lib_path)
	else:
		formatted_gt=read_and_format(tc_or_path, lib_path)
	clean_gt=' '.join([x.strip() for x in generated(formatted_gt.split('\n') ) if x ] )
	
	formatted_gen = read_and_format(gen_path, lib_path)
	clean_gen=' '.join([x.strip() for x in generated(formatted_gen.split('\n')) if x])
	
#	 return levenshtein(clean_gt, clean_gen)
	return clean_gt, clean_gen

def revert_semantic_split(code):
	annotated=re.findall('».*?«', code)
	cleaned = re.findall('»(.*?)«', code)
	cleaned = [i.replace(' ', '') for i in cleaned]
	for i, j in zip (annotated, cleaned):
		try:
			code = code.replace(i,j,1)
		except Exception as e:
			print (str(e))
			print (code)
	return code

def get_nonstandard_ids(log_path):
	with open (log_path)as f:
		log=f.readlines()
	nonstandard=[]
	for l in log:
		m=re.match('Built successfully: \d+_[^0]', l)
		if m:
			nonstandard.append(m.string.split()[-1])
	return nonstandard

def main():
	
	with open(sys.argv[1]) as f:
		meta=json.load(f)
	
	cfg = SimpleNamespace(**meta)
	print(json.dumps(meta, indent=2))
	
	status='status'	
	data={'meta':meta,
		  'skipped':[],
		  'missing':[]}

	
	nonstandard_ids = get_nonstandard_ids(cfg.log_path)
	print(nonstandard_ids)
# print(get_nonstandard_ids('/klonhome/shared/data/apr_neweval/nowy-spsf/plus-gen/console.log'))
	nonstandard_ids_map = {int(x.split('_')[0]):x for x in nonstandard_ids}
	(mappings, revmap) = get_reverse_map(cfg.mappings_path)
	
	with open(cfg.dev_pl) as f:
		gt_lines=[x.strip() for x in f.readlines()]
		
	with open(cfg.generated_dev_pl) as f:
		gen_lines=[x.strip() for x in f.readlines()]
		
	try:
		excluded = cfg.excluded.split(',')
	except AttributeError:
		excluded=[]
		
	def get_template():
		return pd.DataFrame(columns=['tc_id', 'cut', 'method', 'desc', 'line', 'status', 'tc_fullname',])
	gt_data=get_template()
	gen_data=get_template()
	metrics=pd.DataFrame(columns=['cm', '0pr', '0rec', '0f1', '0support', '1pr', '1rec', '1f1', '1support', 'acc', 'cosine',
								'bleu', 'dist_gen_gt', 'lev_ratio', 'codebleu', 'weightedm' , 'syntaxm' , 'flowm', 'tc_fullname', 'gt', 'gen'])
	full_status=pd.DataFrame(columns=['tc_id', 'gt','gen'])
	
	for tc in mappings:
#	for tc in [mappings[787]]:
		fullname=tc["testcase_fullname"]
		tc_id=revmap[fullname]
		
		def is_skip_path(filepath):
			for s in cfg.skip_paths.split(','):
				if s in filepath:
					return True 
			return False

		if (not tc["executable"]) or "@Disabled" in tc["annotations"] or is_skip_path(tc['filepath']): #or "@Disabled" in tc["annotations"]:
			data['skipped'].append(tc_id)
			continue

		(gt_testcase, gen_testcase) = compare_traces(cfg.gt_path,
													 cfg.gen_path,
													 fullname,
													 excluded,
													 subdir=cfg.subdir)
		_full_status=pd.DataFrame({'gt': gt_testcase.status.values, 'gen': gen_testcase.status.values})
		_full_status.insert(0, "tc_id", tc_id)
		full_status = pd.concat([full_status, _full_status], ignore_index=True)
		
		if not os.path.exists((f'{cfg.gen_path}/{fullname}')):
			data['missing'].append(tc_id)
#			 print(f'{tc_id},{fullname},missing')
			continue
		
		def append_tc_data(data, testcase):
			testcase.insert(0, "tc_id", tc_id)
			testcase.insert(6, "tc_fullname", fullname)
			return pd.concat([data, testcase], ignore_index=True)
		
		gt_data = append_tc_data(gt_data, gt_testcase)
		gen_data = append_tc_data(gen_data, gen_testcase)
			
		cm = confusion_matrix(gt_testcase[status], gen_testcase[status])
		cr_json = classification_report(gt_testcase[status], gen_testcase[status], output_dict=True)
		
		cosine_sim = np.dot(gt_testcase[status], gen_testcase[status]) / (np.linalg.norm(gt_testcase[status]) * np.linalg.norm(gen_testcase[status]))
#		cosinesim = cosine_similarity(gt_testcase.status.values.reshape(1,-1), gen_testcase.status.values.reshape(1,-1))

		gt_line = revert_semantic_split(gt_lines[tc_id]) if cfg.revert_sem_split else gt_lines[tc_id]
		gen_line = revert_semantic_split(gen_lines[tc_id]) if cfg.revert_sem_split else gen_lines[tc_id]
		
		references = [gt_line.split()]
		hypothesis = gen_line.split()
		bleu = nltk.translate.bleu_score.sentence_bleu(references, hypothesis) #, smoothing_function=nltk.translate.bleu_score.SmoothingFunction.method1)
		bleu2 = nltk.translate.bleu_score.corpus_bleu([references], [hypothesis]) #, smoothing_function=nltk.translate.bleu_score.SmoothingFunction.method1)
		
		ngram_match_score = cb_bleu.corpus_bleu([references], [hypothesis])
		if (bleu != bleu2) or (bleu != ngram_match_score):
			print("************", bleu, bleu2, ngram_match_score, '************')
			bleu = ngram_match_score
		# calculate weighted ngram match
		keywords = [x.strip() for x in open(f'{cb_path}/keywords/'+cfg.lang+'.txt', 'r', encoding='utf-8').readlines()]
		def make_weights(reference_tokens, key_word_list):
			return {token:1 if token in key_word_list else 0.2 for token in reference_tokens}

		tokenized_refs_with_weights = [[[reference_tokens, make_weights(reference_tokens, keywords)]\
					for reference_tokens in reference] for reference in [references]]	
		weighted_ngram_match_score = weighted_ngram_match.corpus_bleu(tokenized_refs_with_weights,[hypothesis])
		
#		 meteor = nltk.translate.meteor_score.single_meteor_score(gt_line, gen_line)
		
		gen_filename=f'{tc_id}_0.java' if not nonstandard_ids_map.get(tc_id, None) else nonstandard_ids_map[tc_id]
		 # clean_gt, clean_gen = compare_source_code(tc, f'{substitution_dir}/{gen_filename}', lib_path)
		# dist_gt_gen_clean = levenshtein(clean_gt, clean_gen)
		# lev_ratio_clean = Leven.ratio(clean_gen, clean_gt)
		
		dist_gt_gen = levenshtein(gt_line, gen_line)
		lev_ratio = Leven.ratio(gen_line, gt_line)

####	to deleted
		# syntax_match_score_clean = syntax_match.corpus_syntax_match( [[clean_gt]], [clean_gen], lang)
		# dataflow_match_score_clean = dataflow_match.corpus_dataflow_match( [[clean_gt]], [clean_gen], lang)
		#
		# if dataflow_match_score_clean >= 0:
		#	 [alpha, beta, gamma, theta] = [0.25, 0.25, 0.25, 0.25]
		#	 code_bleu_score_clean = alpha*ngram_match_score\
		#					 + beta*weighted_ngram_match_score\
		#					 + gamma*syntax_match_score_clean\
		#					 + theta*dataflow_match_score_clean
		#
		# else:
		#	 print ('ingoring dataflow_match_score')
		#	 [alpha, beta, gamma] = [1/3, 1/3, 1/3]
		#	 code_bleu_score_clean = alpha*ngram_match_score\
		#					 + beta*weighted_ngram_match_score\
		#					 + gamma*syntax_match_score_clean
####  end to delete
		# calculate syntax match
		syntax_match_score = syntax_match.corpus_syntax_match( [[gt_line]], [gen_line], cfg.lang)
		# calculate dataflow match
		dataflow_match_score = dataflow_match.corpus_dataflow_match( [[gt_line]], [gen_line], cfg.lang)
			
#		 print('ngram match: {0}, weighted ngram match: {1}, syntax_match: {2}, dataflow_match: {3}'.\
#							 format(ngram_match_score, weighted_ngram_match_score, syntax_match_score, dataflow_match_score))
		
		if dataflow_match_score >= 0:
			[alpha, beta, gamma, theta] = [0.25, 0.25, 0.25, 0.25]
			code_bleu_score = alpha*ngram_match_score\
							+ beta*weighted_ngram_match_score\
							+ gamma*syntax_match_score\
							+ theta*dataflow_match_score

		else:
			print ('ingoring dataflow_match_score')
			[alpha, beta, gamma] = [1/3, 1/3, 1/3]
			code_bleu_score = alpha*ngram_match_score\
							+ beta*weighted_ngram_match_score\
							+ gamma*syntax_match_score
		
		cr = pd.read_json(StringIO(json.dumps(cr_json)))
		if not "0" in cr.columns:
			print('inserting col 0')
			cr.insert(0, "0", np.nan)
		if not "1" in cr.columns:
			print('inserting col 1')
			cr.insert(1, "1", np.nan)
		metrics.loc[tc_id]=[cm] + cr['0'].tolist() + cr['1'].tolist() + \
							 [cr_json['accuracy'], cosine_sim, bleu, dist_gt_gen, lev_ratio, 
							 code_bleu_score, weighted_ngram_match_score, syntax_match_score, dataflow_match_score, fullname, gt_line, gen_line]
							 
		print(f'{tc_id}, acc:{round(cr_json["accuracy"], 2)}, f1:{round(cr_json["1"]["f1-score"], 2)}, cosine:{round(cosine_sim,2)}, dist:{dist_gt_gen}, lev_ratio: {round(lev_ratio, 2)}, bleu:{round(bleu, 2)}, cb:{round(code_bleu_score, 2)}')
		# pipcb = codebleu.calc_codebleu([gt_line], [gen_line], lang="java", weights=(0.25, 0.25, 0.25, 0.25))
		# if pipcb["dataflow_match_score"]==0:
		#	 pipcb=codebleu.calc_codebleu([gt_line], [gen_line], lang="java", weights=(1/3, 1/3, 1/3, 0))
		#
		# metrics_df.loc[tc_id]=[cm] + cr['1'].tolist() + cr['2'].tolist() + \
		#					  [cr_json['accuracy'], cosine_sim, bleu, dist_gt_gen, lev_ratio, 
		#					  pipcb['codebleu'], pipcb['weighted_ngram_match_score'], pipcb['syntax_match_score'], pipcb['dataflow_match_score'], fullname]
		# print(pipcb)
		# with open('codebleustats.csv', 'a') as f:
		#	 if tc_id == 0:
		#		 f.write(f'method,cb,ngram_match, weighted_ngram_match,syntax_match,dataflow_match,lev_ratio')
		#	 f.write(f'cleaned,{code_bleu_score},{ngram_match_score},{weighted_ngram_match_score},{syntax_match_score},{dataflow_match_score},{lev_ratio}\n')
		#	 f.write(f'pip_codebleu,{pipcb["codebleu"]},{pipcb["ngram_match_score"]},{pipcb["weighted_ngram_match_score"]},{pipcb["syntax_match_score"]},{pipcb["dataflow_match_score"]},\n')
		#	 f.write('\n')
	
	cosine_corpus_compiled = np.dot(gt_data['status'], gen_data['status']) / (np.linalg.norm(gt_data['status']) * np.linalg.norm(gen_data['status']))
	print(f'Cosine corpus level - compiled_subset: {cosine_corpus_compiled}')
	data['meta']['cosine_corpus_compiled']=cosine_corpus_compiled
	
	cosine_corpus_full = np.dot(full_status['gt'], full_status['gen']) / (np.linalg.norm(full_status['gt']) * np.linalg.norm(full_status['gen']))
	print(f'Cosine corpus level - full: {cosine_corpus_full}')
	data['meta']['cosine_corpus_full']=cosine_corpus_full
	
	data['gt_data']=gt_data
	data['gen_data']=gen_data
	data['metrics']=metrics
		
	with open(cfg.out_path, 'wb') as f:
		pickle.dump(data,f)
		
	with open(f'{cfg.out_path}_full_status', 'wb') as f:
		pickle.dump(full_status,f)	
		
if __name__ == '__main__':
	main()   
