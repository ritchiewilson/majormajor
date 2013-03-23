from document import Document
from changeset import Changeset
from op import Op
import socket
import json

from gi.repository import GObject



HOST = ''
PORT = 50007


class Collaborator:
    connections = []

    def __init__(self, doc_id = None):
        self.document = Document(doc_id)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.bind((HOST, PORT))
        GObject.io_add_watch(self.s, GObject.IO_IN, self._listen_callback)


    def _listen_callback(self, source, condition):
        msg, (addr, port) = source.recvfrom(1024*4)
        m = json.loads(msg)
        action = m['action']
        if action == 'announce':
            self.add_connection(m, addr, port)
        if action == 'changesets':
            css = self.build_changesets(m['payload'])
            for cs in css:
                self.recieve_changeset(cs)

        return True

        

    def build_changesets(self, m):
        css = []
        for i in m:
            #TODO actually handle dependencies
            deps = self.document.changesets[:len(self.document.changesets)-3]
            cs = Changeset(i['doc_id'], i['user'],deps)
            for j in i['ops']:
                op = Op(j['action'],j['path'],j['val'],j['offset'])
                cs.add_op(op)
            css.append(cs)
        return css
            
    def add_connection(self, m, addr, port):
        for c in self.connections:
            if c.user == m['user']:
                return

        c = Connection(m['user'], addr, port)
        self.connections.append(c)
        
    def connect(self, signal, callback):
        self.signal_callbacks[signal].append(callback)

    def recieve_changeset(self, cs):
        if not self.document.recieve_changeset(cs):
            return

        for callback in self.signal_callbacks['recieve-changeset']:
            callback()

    signal_callbacks = {
        'recieve-changeset' : [],
        }

    
class Connection:
    def __init__(self, user, addr, port):
        self.user = user
        self.addr = addr
        self.port = port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.connect((addr, port))
        self.s.send('ack')
