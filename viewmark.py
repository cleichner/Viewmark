#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import misaka
import os.path
import sys
import time
import tornado.ioloop
import tornado.web
import webbrowser

from string import Template
from threading import Lock
from tornado import websocket
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# TODO favicon,
# packaging,
# actual logging

page = Template(
'''<!DOCTYPE html>
<html>
<head>
<link rel="stylesheet" type="text/css" href="static/markdown.css">
<script>
    var ws = new WebSocket("ws://localhost:8888/socket");
    ws.onmessage = function(event) {
        document.body.innerHTML = event.data;
    }
</script>
</head>
<body>
$body
</body>
</html>
''')

parser = argparse.ArgumentParser(description='Display Markdown as you edit')
parser.add_argument('file', type=str, help='The file to watch')
args = parser.parse_args()
target_path, target = os.path.split(os.path.abspath(args.file))

# probably not any major risks of not using a lock, but this is multithreaded
# and little hacks have a way of getting out of control.
sockets_lock = Lock()
sockets = set()

class RequestHandler(tornado.web.RequestHandler):
    def get(self):
        with file(target) as f:
            self.write(page.substitute(body=misaka.html(f.read())))

class SocketHandler(websocket.WebSocketHandler):
    def open(self):
        with sockets_lock:
            sockets.add(self)

    def on_close(self):
        with sockets_lock:
            sockets.remove(self)

class DirectoryChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if all([event.is_directory, event.event_type == 'modified',
           event.src_path == target_path]):
            with file(target) as f:
                html = misaka.html(f.read())
                with sockets_lock:
                    for socket in sockets:
                        socket.write_message(html)

observer = Observer()
observer.schedule(DirectoryChangeHandler(), target_path, recursive=True)
observer.start()

application = tornado.web.Application([
    (r"/", RequestHandler),
    (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': 'static'}),
    (r"/socket", SocketHandler),
])

try:
    application.listen(8888)
    webbrowser.open_new_tab('http://localhost:8888')
    tornado.ioloop.IOLoop.instance().start()
except KeyboardInterrupt:
    observer.stop()

observer.join()

