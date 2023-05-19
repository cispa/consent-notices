import csv
import hashlib
import os
import pytesseract
import argparse
from multiprocessing import Pool
from itertools import repeat
from PIL import Image

def get_path(apk, home_dir):
	sha1 = hashlib.sha1()
	sha1.update(apk.encode('utf-8'))
	sha1String = sha1.hexdigest()

	file_path = os.path.join(home_dir, sha1String[0], sha1String[1], sha1String[2], sha1String[3], apk)	

	return file_path


def image_to_string(apk_file_path, screenshot_dir):
	try:
		package_name = os.path.basename(apk_file_path).split('--')[0]	
		print(package_name)
		dir_path = get_path(package_name, screenshot_dir)
		
		if not os.path.isdir(dir_path): return
		image_file_path = os.path.join(dir_path, 'screencap.png')			
		if not os.path.isfile(image_file_path): return	
			
		text_file_path = os.path.join(dir_path, 'screencap.txt')
		if os.path.isfile(text_file_path):
			print(f'Analyzed: {text_file_path}')
			return

		text = pytesseract.image_to_string(image_file_path).replace('\n',' ').strip()	
		
		with open(text_file_path, 'a') as file:
			file.write(text)
	except Exception as e:
		pass

def main():
	ap = argparse.ArgumentParser(description='Convert the app screenshots to text using ORC')	
	ap.add_argument('-apk_path_file', '--apk_path_file', dest='apk_path_file', type=str, required=True)
	ap.add_argument('-screenshot_dir', '--screenshot_dir', dest='screenshot_dir', type=str, required=True)
	args = ap.parse_args()		

	apk_paths = open(args.apk_path_file).read().splitlines()
	print(f'Total number of app: {len(apk_paths)}')

	pool = Pool()
	pool.starmap(image_to_string, zip(apk_paths, repeat(args.screenshot_dir)))	

if __name__ == '__main__':
	main()