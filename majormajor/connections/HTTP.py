# MajorMajor - Collaborative Document Editing Library
# Copyright (C) 2013 Ritchie Wilson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import urllib

try:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from SocketServer import ThreadingMixIn
except:
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from socketserver import ThreadingMixIn
    import urllib.request
import threading
import cgi
import json

from gi.repository import GObject

from .connection import Connection
from ..message import Message


class Handler(BaseHTTPRequestHandler):

    def do_POST(s):
        postvars = {}
        ctype, pdict = cgi.parse_header(s.headers['Content-Type'])
        if ctype == 'multipart/form-data':
            postvars = cgi.parse_multipart(s.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(s.headers['Content-Length'])
            postvars = cgi.parse_qs(s.rfile.read(length), keep_blank_values=1)
        s.send_response(200)
        s.send_header("Content-type", "text/plain")
        s.end_headers()
        s.wfile.write("ack".encode('utf-8'))
        GObject.idle_add(s.server._listen_callback, postvars)

    def do_GET(s):
        """Respond to a GET request."""
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
        body = "<html><head><title>MajorMajor</title></head>" +\
               "<body><h2>MajorMajor</h2>" +\
               "</body></html>"
        s.wfile.write(body.encode('utf-8'))

    def log_message(self, *args):
        """Turn off messages on each request"""
        pass


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    def add_callback(self, _listen_callback):
        """
        Add the callback to the HTTPConnection so incoming messages can be
        passed back to MajorMajor.
        """
        self._listen_callback = _listen_callback


class HTTPConnection(Connection):

    def __init__(self, callback=None):
        self.on_receive_callback = callback
        self._type = "http"
        self.remote_user_addresses = []
        self.host = '127.0.1.1'

        # start at port 8000 and increment through until an availible one is
        # found. Assume and used port in that range is being used by another
        # MajorMajor instance.
        port = 8000
        server = None
        while not server:
            try:
                server = ThreadedHTTPServer((self.host, port), Handler)
            except:
                server = None
                self.remote_user_addresses.append((self.host, port))
                port += 1
        self.listen_port = port

        server.add_callback(self._listen_callback)
        self.server = server
        self.server_thread = threading.Thread(target=server.serve_forever)
        self.server.daemon = True
        self.server_thread.start()
        print("listening at http://127.0.1.1:" + str(port))

    def shutdown(self):
        self.server.shutdown()

    def get_type(self):
        return 'http'

    def get_listen_info(self):
        return {'conn_type': 'http',
                'conn_data': {'port': self.listen_port}}

    def send(self, msg, users=[], broadcast=True):
        ports = []
        if broadcast:
            ports = [x[1] for x in self.remote_user_addresses]
        else:
            ports = [u.get_properties_for_connection(self._type)['port']
                     for u in users if u.has_connection(self.get_type())]

        for port in ports:
            url = "http://127.0.1.1:" + str(port)
            data = self.urlencode_wrapper(msg).encode('utf-8')
            try:
                self.urlopen_wrapper(url, data)
            except Exception as e:
                print("Could not connect to", url)

    def urlencode_wrapper(self, msg):
        try:
            return urllib.urlencode({'payload': msg.to_json()})
        except:
            return urllib.parse.urlencode({'payload': msg.to_json()})

    def urlopen_wrapper(self, url, data):
        try:
            urllib.urlopen(url, data=data)
        except:
            urllib.request.urlopen(url, data=data)

    def _listen_callback(self, payload):

        """
        """

        p = payload['payload'][0] if 'payload' in payload else \
            payload[b'payload'][0].decode('utf-8')

        m = json.loads(p)
        msg = Message(msg=m)
        self.on_receive_callback(msg)
