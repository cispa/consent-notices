import os
import nltk
import numpy as np
import shutil

from string import punctuation
from nltk.corpus import stopwords
from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer
from nltk.stem import SnowballStemmer
from collections import Counter

import sklearn
from sklearn import metrics
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans	 
from scipy.cluster.hierarchy import ward, dendrogram, linkage	
from scipy.cluster import hierarchy
import psycopg2

from langdetect import detect
from autocorrect import Speller

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt	
plt.style.use('ggplot')
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams['figure.dpi'] = 200
plt.rcParams['savefig.dpi'] = 200
plt.rcParams['lines.linewidth'] = 0.5

plt.rcParams['font.weight'] = 'bold'
plt.rcParams['font.size'] = 8
plt.rcParams['legend.fontsize'] = 8
plt.rcParams['figure.titlesize'] = 8
plt.rcParams['hatch.linewidth'] = 0.5

plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42

stopword = stopwords.words('english')
wordnet_lemmatizer = WordNetLemmatizer()
snowball_stemmer = SnowballStemmer('english')
spell = Speller(only_replacements=True)


OUTPUT_CLUSTER_DIR = 'clustered-privacy-related-uis'
IMAGE_INPUT_DIR = 'privacy-related-uis'


def load_data(dir_path = 'privacy-related-uis-text'):
	app_text_dict = dict()
	for file_name in os.listdir(dir_path):
		if not file_name.endswith('.txt'): continue
		package_name = file_name[0:-4]		
		text_content = ''
		with open(os.path.join(dir_path, file_name), 'r') as file:
			text_content = file.read()

		text_content = text_content.lower()
		app_text_dict[package_name] = text_content
	return app_text_dict

def strip_punctuation(word, skipped=None):	
	arrs = []	
	for c in word:
		if c in punctuation or c.isdigit() or not c.isalnum():
			if skipped != None and c == skipped:
				arrs.append('-')		
			else:
				arrs.append('')
		else:
			arrs.append(c)
	
	return ''.join(arrs)

def pre_processing_no_synsets(data):
	content = data.lower()		
	tokens = nltk.word_tokenize(content)						
	tokens = list(set(tokens))

	tokens = [word for word in tokens if not (word.startswith('www.') and word.endswith('.com'))]

	word_tokens = [word for word in tokens if not word.isnumeric()]
	lemmatized_word = [wordnet_lemmatizer.lemmatize(word) for word in word_tokens]
	strip_punctuation_word = [strip_punctuation(word) for word in lemmatized_word]
	removing_stopwords = [word for word in strip_punctuation_word if word not in stopword and word != '' and len(word) > 1]			
	word_tokens = [word for word in removing_stopwords if not word.isnumeric()] 	

	# print(word_tokens)	
	
	stemmed_word = [snowball_stemmer.stem(word) for word in word_tokens]							

	return ' '.join(stemmed_word)

def pre_processing(data):		
	content = data.lower()		
	content = spell(content)
	content = content.replace('informa- tion', 'information')
	content = content.replace('se- curity','security')
	content = content.replace('person- alize','personalize')
	content = content.replace('https://policies  .google.com/technologies/partner-sites',' ')
	tokens = [word for word in content.split(' ') if not (word.startswith('www.') and word.endswith('.com')) and not word.startswith('https') and not word.startswith('http')]
	tokens = [word for word in tokens if not word.isnumeric()]
	tokens = [strip_punctuation(word, skipped='-') for word in tokens] 			
	tokens = [word for word in tokens if '.com' not in word and 'www.' not in word and 'http' not in word and word != 'googlecomtechnologiespartner-sites' and '.html' not in word and word != 'startappcompolicyprivacy-policy'] 	

	# tokens = nltk.word_tokenize(content)						
	tokens = list(set(tokens))	
	word_tokens = [word for word in tokens if not word.isnumeric()]
	lemmatized_word = [wordnet_lemmatizer.lemmatize(word) for word in word_tokens]
	strip_punctuation_word = [strip_punctuation(word) for word in lemmatized_word]
	removing_stopwords = [word for word in strip_punctuation_word if word not in stopword and word != '' and len(word) > 1]			
	word_tokens = [word for word in removing_stopwords if not word.isnumeric()] 		
	# print('---')

	lemma_names = []
	for word in word_tokens:		
		synsets = wn.synsets(word)
		if len(synsets) <= 0:
			continue
		if len(synsets) > 5:
			synsets = synsets[:5]		
		for syn in synsets:
			lemma_names.extend(syn.lemma_names())	
	
	word_tokens.extend(lemma_names)		
	stemmed_word = set([snowball_stemmer.stem(word) for word in word_tokens])
	print(stemmed_word)

	return ' '.join(list(stemmed_word))

def create_dir_exist_remove(url):
	if os.path.isdir(url):
		shutil.rmtree(url)
	os.makedirs(url)

def hierarchial_clustering(app_list, app_text_list):		
	tfidf_vectorizer = TfidfVectorizer(use_idf=True)
	tfidf = tfidf_vectorizer.fit_transform(app_text_list)		

	dist = 1 - cosine_similarity(tfidf)	
	
	linkage_matrix = linkage(dist,'ward')			
	
	max_cut_off_height = 0
	
	for cut_off_height in [max_cut_off_height]:
		# print(f'cut_off_height: {cut_off_height}')
		fig, ax = plt.subplots(figsize=(4, 2)) # set size	
		ax = dendrogram(linkage_matrix, labels=app_text_list, color_threshold=0, above_threshold_color='black')

		plt.ylabel('Height',fontweight='bold')
		plt.xlabel('Consent-Related Dialogs', labelpad=10,fontweight='bold')
		# plt.yticks([cut_off_height],fontsize=8)
		plt.xticks([])
		plt.gca().spines['right'].set_color('none')
		plt.gca().spines['top'].set_color('none')
		plt.gca().spines['bottom'].set_color('none')
		
		plt.axhline(y=cut_off_height, c='red', lw=1, linestyle='dashed')
		plt.savefig(f'dendrogram-{cut_off_height}.png', dpi=200,pad_inches=0,bbox_inches='tight') #save figure as ward_clusters
		
		cut = hierarchy.fcluster(linkage_matrix, t=cut_off_height, criterion='distance')
		cluster_dct = dict((iclus, []) for iclus in np.unique(cut))

		cluster_keyword_dict = dict()
		cluster_name_dict = dict()
		for index,iclus in enumerate(cut):		
			if iclus not in cluster_keyword_dict:
				cluster_keyword_dict[iclus] = set()
			cluster_keyword_dict[iclus].add(app_text_list[index])

		for key in sorted(cluster_keyword_dict):		
			words = []
			for line in cluster_keyword_dict[key]:
				words.extend(line.split(' '))
			counter = Counter(words)		
			common_words = counter.most_common()
			cluster_name = ''
			if len(common_words) == 1:
				letter, count = common_words[0]
				cluster_name = letter
			else:			
				letters = []
				for letter, count in counter.most_common(1):
					letters.append(letter)
				cluster_name = '-'.join(letters)
			cluster_name_dict[key] = str(key) + '-' + cluster_name
			

		cluster_dir_name = f'{OUTPUT_CLUSTER_DIR}-{cut_off_height}'
		create_dir_exist_remove(cluster_dir_name)
		for index,iclus in enumerate(cut):		
			out_dir =  os.path.join(cluster_dir_name, cluster_name_dict[iclus])
			os.makedirs(out_dir, exist_ok=True)
			shutil.copyfile(os.path.join(IMAGE_INPUT_DIR, f'{app_list[index]}.png'), os.path.join(out_dir, f'{app_list[index]}.png'))		


def main():	
	# The app_title_dict, app_developer_dict should be contained the app metadata information. 
	# Depending on how you store this metadata information, you should initialize these variables accordingly.
	# key: package name, value: the corresponding app title
	app_title_dict = dict()
	# key: package name, value: developer name
	app_developer_dict = dict()


	# Getting the privacy-related user interface texts (located in the directory 'privacy-related-uis-text' generated from the previous step)
	app_text_dict = load_data()
	app_list = []
	app_text_list = []
	none_english_apps = set()

	for package_name in app_text_dict:		
		raw_text = app_text_dict[package_name]
		if package_name in app_title_dict:
			app_title = app_title_dict[package_name]			
			if app_title:
				raw_text = raw_text.replace(app_title,' ')			

		if package_name in app_developer_dict:
			app_developer = app_developer_dict[package_name]
			if app_developer:
				raw_text = raw_text.replace(app_developer,' ')			
		
		if detect(raw_text) != 'en': 
			none_english_apps.add(package_name)
			continue
	
		preprocessed_text = pre_processing(raw_text)		

		app_list.append(package_name)
		app_text_list.append(preprocessed_text)			
	
	print(f'Non english apps: {len(none_english_apps)}')		

	hierarchial_clustering(app_list, app_text_list)

if __name__ == '__main__':
	main()	