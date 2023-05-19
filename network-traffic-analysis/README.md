# Automating GDPR Violations Detection

To interact with the app automatically, we extended the DroidBot (lightweight test input generator that sends random or scripted input events/UI interactions to the app) based on our configurations which are consent conditions.


## How to install

```shell
cd droidbot/
pip install -e .
```

If successfully installed, you should be able to execute `droidbot -h`.

## How to use

1. Make sure you have:

    + `Python` (3 are supported).
    + Rooted Android devices (note that all of our testing has been taking place on a Pixel 3a, and Pixel 6 that are running Android 9 or 12).
    + Installing Frida Server for your devices (see this tutorial https://frida.re/docs/android/)
    + Installing mitmproxy for your server as well as the mitmproxy CA certificate has to be installed on the client Android devices (see this documentation https://docs.mitmproxy.org/stable/)

2. After identifying the consent type of the app, then start the following script to run the apps and collect its network traffic based on given consent conditions:

```shell
python network-analysis.py -device 06XAB1Y52M -port 1010 -consent_condition confirm -apk_path_file apk_files.csv -output_dir output -privacy_wording_file privacy_wording.json 
```


| Parameter  | Description |
| ------------- | ------------- |
| -device  | The Android device serial number  |
| -port  | The port of proxy server  |
| -consent_condition  | `confirm` or `reject`  |
| -apk_path_file  | The csv file that contains a list of path to the apk file. For example: each line in this csv file is a `path_to_file/packagename--YYYY-MM-dd.apk`  |
| -output_dir  | The output directory |
| -privacy_wording_file  | The privacy wording file (is included) |

3. All the network traffic will be captured for later analysis of personal data leaks.

## Useful links
- [droidbotApp Source Code](https://github.com/ylimit/droidbotApp)
