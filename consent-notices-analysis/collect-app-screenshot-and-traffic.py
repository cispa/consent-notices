import os
import argparse
import hashlib
import subprocess
import re
import time
import psutil
import signal
from pathlib import Path


def run_cmd(device, cmd):
	cmd_output = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()	
	return cmd_output

def get_installed_apps(device):
	cmd = ['adb', '-s', device, 'shell', 'pm', 'list', 'packages', '-f']
	app_lines = run_cmd(device, cmd).splitlines()
	app_line_re = re.compile("package:(?P<apk_path>.+)=(?P<package>[^=]+)")
	package_to_path = {}
	for app_line in app_lines:
		m = app_line_re.match(app_line)
		if m:
			package_to_path[m.group('package')] = m.group('apk_path')
	return package_to_path

def get_path(apk, home_dir):
	sha1 = hashlib.sha1()
	sha1.update(apk.encode('utf-8'))
	sha1String = sha1.hexdigest()

	file_path = os.path.join(home_dir, sha1String[0], sha1String[1], sha1String[2], sha1String[3], apk)	

	return file_path

def install_app(apk, file_path, device):	
	print(f'Installing {apk}')
	
	install_cmd = ["adb", "-s", device, "install", "-r"]
	install_cmd.append("-g")
	install_cmd.append(file_path)

	install_p = subprocess.Popen(install_cmd, stdout=subprocess.PIPE)
	count = 0
	while apk not in get_installed_apps(device):
		print("Please wait while installing the app...")
		count += 1
		time.sleep(5)		

	return True

def uninstall_app(apk, device):  
	package_name = apk
	if package_name in get_installed_apps(device):
		uninstall_cmd = ["adb", "-s", device, "uninstall", package_name]
		uninstall_p = subprocess.Popen(uninstall_cmd, stdout=subprocess.PIPE)
		while package_name in get_installed_apps(device):
			print("Please wait while uninstalling the app...")
			time.sleep(2)
		uninstall_p.terminate()


def is_mitm_running(listen_port):
	for proc in psutil.process_iter():
		try:
			cmd = ' '.join(proc.cmdline())
			mitm_cmd = f'--set block_global=false --set listen_port={listen_port}'
			if mitm_cmd in cmd:
				return True
		except Exception as e:			
			pass		
	return False

def is_objection_running(device, package_name):
	for proc in psutil.process_iter():
		try:
			cmd = ' '.join(proc.cmdline())
			objection_cmd = f'objection -S {device} -g {package_name}'
			if objection_cmd in cmd:
				return True
		except Exception as e:			
			pass		
	return False


def start_monitor(out_dir_path, out_file_name, listen_port, device, package_name):
	cmd_mitm = f'mitmdump -w {out_dir_path}/{out_file_name} --set block_global=false --set listen_port={listen_port}'
	pro_mitm = subprocess.Popen(cmd_mitm, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid) 													
	cmd_objection = f'objection -S {device} -g {package_name} explore --startup-command "android sslpinning disable"'
	pro_objection = subprocess.Popen(cmd_objection, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)			

	return pro_mitm, pro_objection

def capture_screenshot(device, out_dir_path):
	try:		
		subprocess.Popen(['adb', '-s', device, 'shell', 'uiautomator', 'dump'])
		time.sleep(1)
		subprocess.Popen(['adb', '-s', device, 'pull', '/sdcard/window_dump.xml', out_dir_path])		
	except Exception as e:		
		print(e)
		pass
	try:	
		subprocess.Popen(['adb', '-s', device, 'shell', 'screencap', '-p', '/sdcard/screencap.png'])
		time.sleep(1)
		subprocess.Popen(['adb', '-s', device, 'pull', '/sdcard/screencap.png', out_dir_path])		
	except Exception as e:		
		print(e)
		pass

def tear_down(pro_mitm, pro_objection, listen_port, device, package_name):
	try:
		os.killpg(os.getpgid(pro_mitm.pid), signal.SIGKILL)							
	except Exception as e:		
		print(e)
		pass

	try:
		os.killpg(os.getpgid(pro_objection.pid), signal.SIGKILL)
	except Exception as e:		
		print(e)
		pass

	while is_mitm_running(listen_port):		
		for proc in psutil.process_iter():
			try:
				cmd = ' '.join(proc.cmdline())
				mitm_cmd = f'--set block_global=false --set listen_port={listen_port}'
				if mitm_cmd in cmd:
					proc.terminate()
					os.kill(proc.pid, 9)
					# time.sleep(5)				
					break						
			except Exception as e:				
				pass	
		print('Waiting MITM!!!!!!!!!!!!')

	while is_objection_running(device, package_name):		
		for proc in psutil.process_iter():
			try:
				cmd = ' '.join(proc.cmdline())
				objection_cmd = f'objection -S {device} -g {package_name}'
				if objection_cmd in cmd:
					proc.terminate()
					os.kill(proc.pid, 9)
					# time.sleep(5)				
					break						
			except Exception as e:				
				pass	
		print('Waiting OBJECTION!!!!!!!!!!!!')

def analyze_app(package_name, file_path, device, listen_port, out_dir_path):		
	is_installed = install_app(package_name, file_path, device)
	if not is_installed: return		
	time.sleep(8)

	out_file_name = os.path.basename(file_path)		

	#first time opening the app
	pro_mitm, pro_objection = start_monitor(out_dir_path, out_file_name + '_1', listen_port, device, package_name)		
	time.sleep(10)	
	capture_screenshot(device, out_dir_path)
	tear_down(pro_mitm, pro_objection, listen_port, device, package_name)	

	#uninstall the app
	uninstall_app(package_name, device)	
	

def main():
	ap = argparse.ArgumentParser(description='Dynamic analysis to collect the app screenshot and capture network transmission data without interactions')	
	ap.add_argument('-apk_path_file', '--apk_path_file', dest='apk_path_file', type=str, required=True)
	ap.add_argument('-device', '--device', dest='device', type=str, required=True)
	ap.add_argument('-port', '--port', dest='port', type=int, required=True)
	ap.add_argument('-output_dir', '--output_dir', dest='output_dir', type=str, required=True)
	args = ap.parse_args()		
	
	apk_paths = open(args.apk_path_file).read().splitlines()		
	
	print(f'Total number of app: {len(apk_paths)}')		
	apk_paths.sort()		
	
	for apk_file_path in apk_paths:	
		# File name format: packagename--YYYY-MM-dd.apk, for example: com.cradley.ramp.car.game--2022-04-23.apk
		package_name = os.path.basename(apk_file_path).split('--')[0]

		out_dir_path = get_path(package_name, args.output_dir)	
		if os.path.isdir(out_dir_path):
			print(f'{package_name} is analyzed!')
			continue		

		Path(out_dir_path).mkdir(parents=True, exist_ok=True)
		analyze_app(package_name, apk_file_path, args.device, args.port, out_dir_path)
		
if __name__ == '__main__':
	main()