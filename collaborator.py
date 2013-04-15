from document import Document
from changeset import Changeset
from op import Op
import socket
import json
import sys
import uuid

from gi.repository import GObject, Gtk, GdkPixbuf



HOST = '<broadcast>'
PORT = 8000
DEFAULT_COLLABORATOR_PORT = 8080
if len(sys.argv) > 1:
    PORT = int(sys.argv[1])
    DEFAULT_COLLABORATOR_PORT = 8000


class Collaborator:
    documents = []
    connections = []
    default_user = str(uuid.uuid4())

    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.s.bind((HOST, PORT))
        GObject.io_add_watch(self.s, GObject.IO_IN, self._broadcast_listen_callback)
        self.announce()
        

    def new_document(self, doc_id=None, user=default_user):
        d = Document(doc_id, user)
        self.documents.append(d)
        #self.announce()
        return d

    def get_document(self, doc_id):
        for doc in self.documents:
            if doc.get_id() == doc_id:
                return doc
        return None

    def add_local_op(self, doc, op):
        doc.add_op(op)
        doc.close_changeset()
        cs = doc.get_last_changeset()
        self.send_changeset(cs)

    def send_changeset(self, cs):
        msg = {'action':'changeset',
               'payload':cs.to_dict(),
               'cs_id': cs.get_id(),
               'user':cs.get_user(),
               'doc_id':cs.get_doc_id()}
        jmsg = json.dumps(msg)
        #for c in self.connections:
        #    c.send(jmsg)
        self.broadcast(msg)
        
    def _listen_callback(self, source, condition):
        msg, (addr, port) = source.recvfrom(1024*4)
        m = json.loads(msg)
        for doc in self.documents:
            if doc.get_user() == m['user']:
                return
        action = m['action']
        if action == 'announce':
            self.add_connection(m, addr, port)
            self.invite_to_document(m['user'], self.documents[0].get_user(),
                                    self.documents[0].get_id())
        if action == 'changeset':
            self.recieve_changeset(m)
        if action == 'cursor':
            self.update_cursor(m)
        if action == 'invite_to_document':
            self.accept_invitation_to_document(m)
        if action == 'request_snapshot':
            self.send_snapshot(m)
        if action == 'send_snapshot':
            self.recieve_snapshot(m)

        for doc in self.documents:
            print doc.get_id()
            print doc.get_snapshot()
        return True

    def send_snapshot(self, m):
        doc = self.get_document(m['doc_id'])
        deps = doc.get_last_changeset()
        deps = deps.to_dict() if deps else None
        msg = {'action': 'send_snapshot',
               'doc_id': doc.get_id(),
               'user': doc.get_user(),
               'section': 1,
               'sections': 1,
               'snapshot': doc.get_snapshot(),
               'deps': deps}
        print msg
        self.broadcast(msg)

    def recieve_snapshot(self, m):
        doc = self.get_document(m['doc_id'])
        doc.set_snapshot(m['snapshot'], m['deps'])
        for callback in self.signal_callbacks['recieve-snapshot']:
            callback()
        
    def accept_invitation_to_document(self, m):
        doc = self.new_document(m['doc_id'])
        self.request_snapshot(m['doc_id'])
        for callback in self.signal_callbacks['accept-invitation']:
            callback(doc)
    
    def request_snapshot(self, doc_id):
        doc = self.get_document(doc_id)
        msg = {'action':'request_snapshot',
               'user': doc.get_user(),
               'doc_id': doc_id}
        self.broadcast(msg)
        
    def _direct_listen_callback(self, source, condition):
        self._listen_callback(source, condition)
        return True
    
    def _broadcast_listen_callback(self, source, condition):
        self._listen_callback(source, condition)
        return True
        
    def update_cursor(self, msg):
        for c in self.connections:
            if c.user == msg['user']:
                if c.cursor['stamp'] < msg['cursor']['stamp']:
                    c.cursor = msg['cursor']
                break
        for callback in self.signal_callbacks['remote-cursor-update']:
            callback()
            
    def announce(self):
        msg = {'action':'announce',
               'user':self.default_user}
        self.broadcast(msg)

    def invite_to_document(self, to_user, from_user, doc_id):
        msg = {"action":"invite_to_document",
               "to_user":to_user,
               "user":from_user,
               "doc_id":doc_id}
        self.broadcast(msg)
        
    def broadcast(self, msg):
        ports = [DEFAULT_COLLABORATOR_PORT]
        for c in self.connections:
            if not c.port in ports: port.append(c.port)
        for port in ports:
            self.s.sendto(json.dumps(msg), (HOST, port))

    
    def build_changeset(self, m):
        doc = self.get_document(m['doc_id'])
        if not doc:
            return

        p = m['payload']
        last_dep = doc.get_changeset_by_id(p['dep'])
        deps = [] if last_dep == None else last_dep.get_deps() + [last_dep]
        cs = Changeset(p['doc_id'], p['user'],deps)
        #cs.set_id(m['cs_id'])
        for j in p['ops']:
            op = Op(j['action'],j['path'],j['val'],j['offset'])
            cs.add_op(op)
        return cs
            
    def add_connection(self, m, addr, port):
        for c in self.connections:
            if c.user == m['user']:
                c.update(addr, port)
                #c.send('known')
                return

        c = Connection(m['user'], addr, port)
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
        'recieve-snapshot' : [],
        'remote-cursor-update' : [],
        'accept-invitation': [],
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

    def _listen_callback(self, msg):
        print msg

    
