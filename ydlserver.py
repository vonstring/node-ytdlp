#!/usr/bin/env python
from __future__ import print_function
from __future__ import unicode_literals
import sys
import os
import json
try:
    args = json.loads(sys.argv[1])
except:
    args = {}
ydl_path = args.get("ytdlpPath", os.path.join(os.path.dirname(__file__), "yt-dlp"))
ffmpeg_path = args.get("ffmpegPath")
import random
import string
import traceback
import tempfile

import zipimport


def log(*args):
    print("|YDLSERVER|", *args, file=sys.stderr)
    sys.stderr.flush()

log("ydl_path",repr(ydl_path))
sys.path.insert(0, ydl_path)
#sys.meta_path.insert(1, zipimport.zipimporter(ydl_path))
import yt_dlp as youtube_dl

def generate_id():
    return ''.join([random.choice(string.ascii_letters+string.digits+'-_') for ch in range(8)])

class Session:
    def __init__(self):
        self.current_id = None

    def handle_data(self, data):
        log(data)
        try:
            data = json.loads(data)
            self.current_command=data.pop("command")
            self.current_id = data.pop("id", None)
            getattr(self, "command_%s" % self.current_command)(**data)
        except Exception as e:
            self.error(e)

    def run_loop(self):
        self.msg("ready")
        for line in iter(sys.stdin.readline, ''):
            self.handle_data(line.strip())

    def msg(self, msg_type, data=None):
        payload = {
            "type": msg_type,
            "data": data,
        }
        if self.current_id is not None:
            payload["id"] = self.current_id
        self.send(payload)

    def send(self, data):
        sys.stdout.write(json.dumps(data, default=lambda x: None)+"\n")
        sys.stdout.flush()

    def error(self, exception):
        log(traceback.format_exc())
        self.send({
            "error":exception.__class__.__name__,
            "message":str(exception),
            "type":"error",
        })
    
    def handle_progress(self, progress_data):
        self.msg("progress", progress_data)

    def _ydl(self, url=None, options=None):
        options = options or {}
        download = options.get("download", True)
        path = ""
        if download:
            path = tempfile.mkdtemp(suffix="-ydl")
        log("tmpdir: %s" % path)
        ydl_opts = {
            "format":"bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
            "quiet":True,
            "noprogress":True,
            #"no_check_certificate":True,
            "concurrent_fragment_downloads":5,
            "outtmpl":os.path.join(path, "%(title).150s-%(id)s.%(ext)s"),
        }
        log(ydl_opts)
        if ffmpeg_path is not None:
            ydl_opts["ffmpeg_location"] = ffmpeg_path
        if options is not None:
            ydl_opts.update(options)

        ydl = youtube_dl.YoutubeDL(ydl_opts)
        if download:
            ydl.add_progress_hook(self.handle_progress)
        try:
            info_dict = ydl.extract_info(url, download=download)
        except Exception as e:
            raise e
        info = {}
        for k in info_dict.keys(): #["thumbnail", "duration", "title"]:
            info[k] = info_dict.get(k)
        tmpfn = ydl.prepare_filename(info_dict)
        log("tmp fn: "+tmpfn)
        info["tmpfn"] = tmpfn
        #info["destpath"] = destpath
        #info["options"] = options

        return info
    
    def send_result(self, result=None, exception=None):
        result = result or {}
        if exception:
            result.update({    
                "error":exception.__class__.__name__,
                "message":str(exception),
            })
        self.msg(self.current_command, result)

    def command_download(self, url=None, options=None):
        options = options or {}
        options["download"] = True
        try:
            info = self._ydl(url, options)
        except Exception as e:
            self.send_result(exception=e)
            return

        self.send_result({
            "info":info,
        })

    def command_info(self, url=None, options=None):
        options = options or {}
        options["download"] = False
        try:
            info = self._ydl(url, options)
        except Exception as e:
            self.send_result(exception=e)
            return

        self.send_result({
            "info":info,
        })

    def command_version(self):
        self.send_result({
            "version":youtube_dl.version.__version__
        })
        
def main():
    log("Youtube-dl server started")
    log("youtube-dl binary loaded from", ydl_path, youtube_dl.version.__version__, youtube_dl.__file__)
    if ffmpeg_path:
        log("ffmpeg binary set to", ffmpeg_path)
    session = Session()
    session.run_loop()

def end():
    log("Youtube-dl server closing")

if __name__ == "__main__":
    main()