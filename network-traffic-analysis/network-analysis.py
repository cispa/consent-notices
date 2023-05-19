import os
import argparse
import subprocess
from pathlib import Path

def start_droidbot(device_serial, device_port, apk_file_path, consent_condition, output_dir, privacy_wording_file):
	package_name = os.path.basename(apk_file_path).split('--')[0]		
	Path(output_dir).mkdir(parents=True, exist_ok=True)	
	
	droidbot_cmd = ["droidbot", "-a", apk_file_path, \
							"-o", output_dir, \
							"-d", device_serial, \
							"-policy", "mitm", \
							"-interval", "1", \
							"-grant_perm", \
							"-keep_env", \
							"-accessibility_auto", \
							"-timeout", "150", \
							"-consent_condition", consent_condition, \
							"-privacy_wording_file", privacy_wording_file]		

	process = subprocess.call(droidbot_cmd)	

def main():
	parser = argparse.ArgumentParser(description="Start DroidBot to test an Android app.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument("-device", action="store", dest="device", required=True, help="The serial number of target device (use `adb devices` to find)")
	parser.add_argument('-port', '--port', dest='port', type=int, required=True)	
	parser.add_argument("-consent_condition", action="store", dest="consent_condition", required=True, help="The consent condition")
	parser.add_argument('-apk_path_file', '--apk_path_file', dest='apk_path_file', type=str, required=True)
	parser.add_argument('-output_dir', '--output_dir', dest='output_dir', type=str, required=True)
	parser.add_argument('-privacy_wording_file', '--privacy_wording_file', dest='privacy_wording_file', type=str, required=True)
	

	args = parser.parse_args()   
    
	apk_paths = open(args.apk_path_file).read().splitlines()		
	print(f'Total number of app: {len(apk_paths)}')		
	apk_paths.sort()		
	
	for apk_file_path in apk_paths:
		start_droidbot(args.device, args.port, apk_file_path, args.consent_condition, args.output_dir, args.privacy_wording_file)					

if __name__ == '__main__':
	main()