#!/usr/bin/env python
# -*- coding: utf-8 -*-

import misaka
import sys
import time
import tornado.ioloop
import tornado.web

from string import Template
from tornado import websocket
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# TODO favicon, static css serving, parsing command line args, packaging,
# good variable names

page = Template(
'''<!DOCTYPE html>
<html>
<head>
<link href="http://kevinburke.bitbucket.org/markdowncss/markdown.css" rel="stylesheet"></link>
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

target = 'hello.md'
target_path = '/Users/chas/code/python/viewmark'

sockets = set()

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        with file(target) as f:
            self.write(
                page.substitute(
                    body = misaka.html(
                        f.read()
                    )
                )
            )

class ClientSocket(websocket.WebSocketHandler):
    def open(self):
        sockets.add(self)
        print "WebSocket opened"

    def on_close(self):
        sockets.remove(self)
        print "WebSocket closed"

class MyEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if all([event.is_directory, event.event_type == 'modified',
           event.src_path == target_path]):
            with file(target) as f:
                html = misaka.html(f.read())
                for socket in sockets:
                    socket.write_message(html)

event_handler = MyEventHandler()
observer = Observer()
observer.schedule(event_handler, target_path, recursive=True)
observer.start()

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/socket", ClientSocket),
])

try:
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
except KeyboardInterrupt:
    observer.stop()

observer.join()

