# coub-dl-liked
Download your liked videos from coub.com. 

Program downloads mp3, mp4 files and combines them together using `ffmpeg`. All videos will be looped to the length of an audio file. Pages with an info about your liked videos will be saved to json dump: `likes.json`, any future runs will use that instead of an API. In case of multiple sequential runs, it doesn't re-download already downloaded videos, comparison based on filenames only.

### How to use it
Install python

Install dependencies:
```
pip install -r requirements.txt
```
Install [ffmpeg](https://ffmpeg.org/) programm ([Windows detailed instruction](https://www.geeksforgeeks.org/how-to-install-ffmpeg-on-windows/))

Go to https://coub.com/api/v2/users/me and find your `api_token`: a long sequence of characters, copy it

Now you're ready to download your sweet COUB's:

Windows:
```
cd coub-dl-liked
set API_TOKEN=your_long_token
# you could set audio and video quality preference
# set VIDEO_QUALITY=high     available values: higher, high, med; default - high
# set AUDIO_QUALITY=high     available values: high, med; default - high
python .\download_liked_coubs.py
```
Linux&MAC:
```
cd coub-dl-liked
API_TOKEN=your_long_token VIDEO_QUALITY=high AUDIO_QUALITY=high python ./download_liked_coubs.py
```

All video loops would be downloaded to `/videos` directory.

Disk usage estimation: 1000 higher quality videos ~38 GB

Tested on Windows 10, Ubuntu 20.04, python 3.10.3
