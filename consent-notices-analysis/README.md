# Source code for: Freely Given Consent? Studying Consent Notice of Third-Party Tracking and Its Violations of GDPR in Android Apps

## Prerequisite
1. `Python` (3 are supported).
2. Rooted Android devices (note that all of our testing has been taking place on a Pixel 3a, and Pixel 6 that are running Android 9 or 12).
3. Installing Frida Server for your devices (see this tutorial https://frida.re/docs/android/)
4. Installing mitmproxy for your server as well as the mitmproxy CA certificate has to be installed on the client Android devices (see this documentation https://docs.mitmproxy.org/stable/)


## Step 1: Collecting app screenshot and network traffic without any interactions
1. Start the Frida server on your Android devices.
2. Start the mitmproxy on your server machine and change the network setting on your Android devices to your Proxy server
3. Run the following script to run the app in question to take screenshot and further collect the app's network traffic (without any interactions)

```shell
python collect-app-screenshot-and-traffic.py -apk_path_file apk_files.csv -device 06XAB1Y52M -port 1010 -output_dir output/
```

| Parameter  | Description |
| ------------- | ------------- |
| -device  | The Android device serial number  |
| -port  | The port of proxy server  |
| -apk_path_file  | The csv file that contains a list of path to the apk file. For example: each line in this csv file is a `path_to_file/packagename--YYYY-MM-dd.apk`  |
| -output_dir  | The output directory |


## Step 2: Extracting text from the apps' screenshots using ORC
1. Run the following script to extract the text from the collected apps' screenshots. The extracted text will be located in the same directory of the corresponding apps' screenshots.

```shell
python convert-screenshot-to-text.py -apk_path_file apk_files.csv -screenshot_dir output/
```

| Parameter  | Description |
| ------------- | ------------- |
| -apk_path_file  | The csv file that contains a list of path to the apk file. For example: each line in this csv file is a `path_to_file/packagename--YYYY-MM-dd.apk`  |
| -screenshot_dir  | The output directory of Step 1 (contains the collected apps' screenshots)|


## Step 3: Identifying privacy-related user interfaces using string-matching technique
1. Run the following script to identify privacy-related user interfaces. The identified privacy-related user interfaces will be extracted to `privacy-related-uis` and the corresponding text will be located in `privacy-related-uis-text`, these two directories will be automatically created after running the script.

```shell
python identifying-privacy-related-ui.py -apk_path_file apk_files.csv -screenshot_dir output/
```

| Parameter  | Description |
| ------------- | ------------- |
| -apk_path_file  | The csv file that contains a list of path to the apk file. For example: each line in this csv file is a `path_to_file/packagename--YYYY-MM-dd.apk`  |
| -screenshot_dir  | The output directory of Step 1 (contains the collected apps' screenshots)|


## Step 4: Clustering the identified privacy-related user interfaces
1. Run the following script to perform the clustering of privacy-related user interfaces. See the code comments for more details. The results will be located in `clustered-privacy-related-uis` directory. In this script the `max_cut_off_height` is set to 0 (resulted in maximum number of clusters), however, in practice, we should choose it accordingly based on the dendrogram and our quality measurement.

```shell
python clustering-privacy-related-ui.py
```