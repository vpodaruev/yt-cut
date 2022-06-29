#!/usr/bin/env python3

import json
import subprocess as sp
from urllib.parse import urlparse

from utils import *


global args  # set in main module

class NotYoutubeURL(RuntimeError):
    def __init__(self, url):
        super().__init__(f"'{url}' is not a youtube URL")


class YoutubeVideo:
    def __init__(self, url):
        netloc = urlparse(url).netloc
        if all([item not in netloc for item in {"youtube.com", "youtu.be"}]):
            raise NotYoutubeURL(url)
        p = sp.run([f"{args.youtube_dl}", "--dump-json", f"{url}"],
                    capture_output=True, encoding="utf-8", check=True)
        js = json.loads (p.stdout.strip())
        self.url = url
        self.title = js["title"]  if "title" in js  else "Video Title"
        self.channel = js["channel"]  if "channel" in js  else "Youtube Channel"
        self.duration = to_hhmmss(js["duration"])  if "duration" in js  else "0"
    
    def download_urls(self):
        p = sp.run([f"{args.youtube_dl}", "-g", f"{self.url}"],
                    capture_output=True, encoding="utf-8", check=True)
        return p.stdout.split()
    
    def download(self, filename, start, end):
        video, audio = self.download_urls()
        sp.run ([f"{args.ffmpeg}", "-y", "-loglevel", "quiet",
                 "-ss", f"{start}", "-to", f"{end}", "-i", f"{video}",
                 "-ss", f"{start}", "-to", f"{end}", "-i", f"{audio}",
                 "-c", "copy", f"{filename}"],
                 stdin=sp.DEVNULL, stdout=sp.DEVNULL, stderr=sp.DEVNULL, check=True)
