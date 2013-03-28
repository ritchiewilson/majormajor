from document import Document
from changeset import Changeset
from op import Op
import socket
import json

from gi.repository import GObject, Gtk, GdkPixbuf



HOST = '<broadcast>'
PORT = 8080


class Collaborator:
    documents = []
    connections = []
    

    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.s.bind((HOST, PORT))
        print PORT
        GObject.io_add_watch(self.s, GObject.IO_IN, self._listen_callback)
        self.announce()

    def new_document(self, doc_id=None):
        d = Document(doc_id)
        self.documents.append(d)
        return d

    def get_document(self, doc_id):
        for doc in self.documents:
            if doc.get_id() == doc_id:
                return doc
        #TODO for testing, just return some doc. probably one and only
        return self.documents[0]
        return None
        
    def _listen_callback(self, source, condition):
        print 'heard'
        msg, (addr, port) = source.recvfrom(1024*4)
        print addr
        m = json.loads(msg)
        action = m['action']
        if action == 'announce':
            self.add_connection(m, addr, port)
        if action == 'changeset':
            self.recieve_changeset(m)
        if action == 'cursor':
            self.update_cursor(m)
        return True
    
    def update_cursor(self, msg):
        for c in self.connections:
            if c.user == msg['user']:
                if c.cursor['stamp'] < msg['cursor']['stamp']:
                    c.cursor = msg['cursor']
                    print 'did it'
                break
        for callback in self.signal_callbacks['remote-cursor-update']:
            callback()
            
    def announce(self):
        users = []
        doc_ids = []
        for doc in self.documents:
            users.append(doc.get_user())
            doc_ids.append(doc.get_id())
            
        msg = {'action':'announce',
               'users':users,
               'doc_ids': doc_ids}
        self.s.sendto(json.dumps(msg), (HOST, PORT))
        

    def build_changeset(self, m):
        doc = self.get_document(m['doc_id'])
        if not doc:
            return
        
        #TODO actually handle dependencies
        deps = doc.changesets[:len(doc.changesets)-3]
        cs = Changeset(m['doc_id'], m['user'],deps)
        for j in m['ops']:
            op = Op(j['action'],j['path'],j['val'],j['offset'])
            cs.add_op(op)
        return cs
            
    def add_connection(self, m, addr, port):
        for doc in self.documents:
            if doc.get_user() == m['users']:
                return
        for c in self.connections:
            if c.user == m['users']:
                c.update(addr, port)
                c.send('known')
                return

        c = Connection(m['users'], addr, port)
        self.connections.append(c)
        c.send('learned');
        
    def connect(self, signal, callback):
        self.signal_callbacks[signal].append(callback)

    def recieve_changeset(self, m):
        doc = self.get_document(m['doc_id'])
        if not doc:
            return
        
        cs = self.build_changeset(m)
        if not doc.recieve_changeset(cs):
            return

        for callback in self.signal_callbacks['recieve-changeset']:
            callback()

    signal_callbacks = {
        'recieve-changeset' : [],
        'remote-cursor-update' : [],
        }

    
class Connection:
    addr = None
    port = None
    cursor = {'stamp':0, 'path':[], 'offset':0}

    def __init__(self, user, addr, port):
        self.user = user
        self.update(addr, port)

    def send(self, msg):
        self.s.send(msg)

    def update(self, addr, port):
        if self.addr != addr or self.port != port:
            self.addr = addr
            self.port = port
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.connect((addr, port))

