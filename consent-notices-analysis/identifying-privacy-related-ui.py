import json
import hashlib
import argparse
import os
import shutil
import xml.etree.ElementTree as ET
from multiprocessing import Pool
from itertools import repeat

def get_path(apk, home_dir):
	sha1 = hashlib.sha1()
	sha1.update(apk.encode('utf-8'))
	sha1String = sha1.hexdigest()

	file_path = os.path.join(home_dir, sha1String[0], sha1String[1], sha1String[2], sha1String[3], apk)	

	return file_path

def get_privacy_wordings(file_input = 'privacy_wording.json'):
	word_set = set()
	with open(file_input) as file:
		word_dict = json.load(file)
	for country in word_dict:
		word_set.update(country['words'])
	return word_set

def read_string_resources(file_input):
	string_res = set() 
	try:
		tree = ET.parse(file_input)
		for child in tree.getroot():			
			string_res.add(child.text.lower())
	except Exception as e:
		pass
	return string_res

def identifying_privacy_setting(apk_file_path, privacy_word_set, screenshot_dir):		
	package_name = os.path.basename(apk_file_path).split('--')[0]	
	# print(package_name)
	dir_path = get_path(package_name, screenshot_dir)
	
	if not os.path.isdir(dir_path): return
	image_file_path = os.path.join(dir_path, 'screencap.txt')	
	if not os.path.isfile(image_file_path): return
	text_content = ''
	with open(image_file_path, 'r') as file:
		text_content = file.read()

	text_content = text_content.lower()
	found = False
	for privacy_word in privacy_word_set:		
		if privacy_word in text_content:
			found = True
			break
	if found:		
		print(package_name, flush = True)
		os.makedirs('privacy-related-uis')
		os.makedirs('privacy-related-uis-text')
		shutil.copyfile(os.path.join(dir_path, 'screencap.png'), os.path.join('privacy-related-uis', package_name + '.png'))
		shutil.copyfile(os.path.join(dir_path, 'screencap.txt'), os.path.join('privacy-related-uis-text', package_name + '.txt'))

def main():
	ap = argparse.ArgumentParser(description='Convert the app screenshots to text using ORC')	
	ap.add_argument('-apk_path_file', '--apk_path_file', dest='apk_path_file', type=str, required=True)
	ap.add_argument('-screenshot_dir', '--screenshot_dir', dest='screenshot_dir', type=str, required=True)
	args = ap.parse_args()		

	apk_paths = open(args.apk_path_file).read().splitlines()
	print(f'Total number of app: {len(apk_paths)}')

	privacy_word_set = get_privacy_wordings()	

	pool = Pool()
	pool.starmap(identifying_privacy_setting, zip(apk_paths, repeat(privacy_word_set), repeat(args.screenshot_dir)))
	

if __name__ == '__main__':
	main()