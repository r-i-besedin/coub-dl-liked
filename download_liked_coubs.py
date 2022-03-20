from datetime import datetime
import os
import urllib
import urllib.request
import aiohttp
import soundfile as sf
import json
import traceback
import asyncio
import subprocess
import logging
import sys

PAGES_DUMP_JSON_FILENAME = 'likes.json'

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.FileHandler(f"{datetime.now().strftime('%d-%b-%Y %H_%M_%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

async def get_likes_page_as_json(session, i, api_token):
    logging.debug(f"Fetching page {i}")
    async with session.get(f"https://coub.com/api/v2/timeline/likes?page={i}&per_page=25&api_token={api_token}") as response:
        return await response.json()

async def save_likes_pages():
    # https://coub.com/api/v2/users/me
    api_token = os.getenv("API_TOKEN")
    if api_token is None:
        sys.exit("API_TOKEN environment variable must be specified")
    # async fetch all "pages" with liked videos info
    async with aiohttp.ClientSession() as session:
        total_pages = (await get_likes_page_as_json(session, 1, api_token))['total_pages']
        logging.info(f"Total page count: {total_pages}")
        logging.info("Fetching all pages...")
        pages = await asyncio.gather(*(get_likes_page_as_json(session, i, api_token) for i in range(1, total_pages+1)))
        logging.info(f"{len(pages)} pages fetched")
    # save fetched info
    with open(PAGES_DUMP_JSON_FILENAME, 'w') as f:
        json.dump(pages, f)
    logging.info(f"COUB's info dumped to a file")

def get_coubs_from_likes_pages_dump():
    with open(PAGES_DUMP_JSON_FILENAME, 'r') as f:
        pages = json.load(f)
    logging.info(f"COUB's info loaded from a file")

    coubs = []
    for i in range(len(pages)):
        coubs = coubs + pages[i]['coubs']
    logging.info(f'Total COUB\'s video count: {len(coubs)}')
    return coubs

def delete_file_if_exists(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)

async def main():
    if not os.path.exists(PAGES_DUMP_JSON_FILENAME):
        await save_likes_pages()

    coubs = get_coubs_from_likes_pages_dump()

    proceed = input("Proceed to download. y/n (y) ")
    if len(proceed) != 0 and proceed.lower() != 'y':
        exit(0)
    
    # download liked videos to dir videos/
    for i, coub in enumerate(coubs):
        try:
            id = coub['permalink']
            logging.info(f"Downloading video {i+1}, permalink: {id}")

            out_video_fpath = os.path.join('videos', f'{id}.mp4')
            out_video_fname_tmp = f'{id}_tmp.mp4'
            out_wav_fname = f'{id}.wav'

            if os.path.exists(out_video_fpath):
                logging.info(f"{out_video_fpath} already exists")
                continue

            video_url = coub['file_versions']['html5']['video']['high']['url']
            video_fname = video_url.split('/')[-1]

            # there could be coub's without audio
            if 'audio' not in coub['file_versions']['html5']:
                urllib.request.urlretrieve(video_url, out_video_fpath)
                continue

            mp3_url = coub['file_versions']['html5']['audio']['high']['url']
            mp3_fname = mp3_url.split('/')[-1]

            urllib.request.urlretrieve(mp3_url, mp3_fname)
            urllib.request.urlretrieve(video_url, video_fname)

            # convert mp3 to wav
            subprocess.run(['ffmpeg', '-i', mp3_fname, '-vn', '-acodec', 'pcm_s16le', 
                '-ac', '2', '-ar', '44100', '-f', 'wav', out_wav_fname], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).check_returncode()
            # read wav and get file len in seconds
            x, sr = sf.read(f'{out_wav_fname}')
            wav_len = len(x)/sr
            # loop video to duration of file len
            subprocess.run(['ffmpeg', '-stream_loop', '-1', '-t', str(wav_len), 
                '-i', video_fname, '-c', 'copy', out_video_fname_tmp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).check_returncode()
            
            # combine MP3 with looped video, add metadata
            channel_title = coub['channel']['title']
            channel_permalink = coub['channel']['permalink']
            tags = []
            for tag in coub['tags']:
                tags.append(tag['title'])
            tags_str = ';'.join(tags)
            comment = 'Author: %s\nLink: %s\nOriginal video: %s\nTags: %s' % (
                    channel_title,
                    f'https://coub.com/{channel_permalink}',
                    f'https://coub.com/view/{id}',
                    tags_str)
            title = coub['title']
            subprocess.run(["ffmpeg", "-i", out_video_fname_tmp, "-i", mp3_fname, 
                                    "-metadata", "title=%s" % title,
                                    "-metadata", "comment=%s" % comment,
                                    "-c:v", "copy", "-c:a", "aac", out_video_fpath], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).check_returncode()
        except Exception as e:
            logging.error(f'Failed to process video {id}')
            logging.error(traceback.format_exc())
        finally:
            delete_file_if_exists(out_video_fname_tmp)
            delete_file_if_exists(video_fname)
            delete_file_if_exists(out_wav_fname)
            delete_file_if_exists(mp3_fname)

if __name__ == '__main__':
    asyncio.run(main())