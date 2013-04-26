from document import Document
from changeset import Changeset
from op import Op
import socket
import json
import sys
import uuid
import datetime

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
    # TODO: user authentication
    default_user = str(uuid.uuid4())
    big_insert = False

    def __init__(self):
        """
        On creation, create a socket to listen to UDP broadcasts on a
        default port.
        TODO: change this to a "connection" abstracion
        """
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.s.bind((HOST, PORT))
        GObject.io_add_watch(self.s, GObject.IO_IN, self._listen_callback)
        #GObject.timeout_add(7, self.test_thousands_ops)
        GObject.timeout_add(10, self.close_open_changesets)
        self.announce()

    def test_thousands_ops(self):
        if self.big_insert:
            self.documents[0].add_local_op(Op('si',[],offset=0,val='s'))
            self.documents[0].close_changeset()
            for callback in self.signal_callbacks['recieve-snapshot']:
                callback()
        return True

    def close_open_changesets(self):
        for doc in self.documents:
            oc = doc.get_open_changeset()
            if oc and not oc.is_empty():
                cs = doc.close_changeset()
                self.send_changeset(cs)
        return True
                
            
            

    def new_document(self, doc_id=None, user=default_user, snapshot=None):
        """
        Create a new Document to add to the list of open
        documents. When no doc_id is provided, a random one will be
        assigned. When no user is defined, the default is used.
        TODO: should split this up into new_document and open_document
        """
        d = Document(doc_id, user, snapshot)
        self.documents.append(d)
        return d

    def get_document(self, doc_id):
        """
        A Collaborator can hold multiple documents. Get the relevent
        document by doc_id.
        """
        for doc in self.documents:
            if doc.get_id() == doc_id:
                return doc
        return None

    def add_local_op(self, doc, op):
        """
        Add an opperation to the given doc.

        TODO: is this worthless? Should be part of document.
        """
        doc.add_local_op(op)
        doc.close_changeset()
        cs = doc.get_last_changeset()
        self.send_changeset(cs)

    def send_changeset(self, cs):
        """
        Build the message object to send to other collaborators.
        """
        msg = {'action':'changeset',
               'payload':cs.to_dict(),
               'cs_id': cs.get_id(),
               'user':cs.get_user(),
               'doc_id':cs.get_doc_id()}
        self.broadcast(msg)
        
    def _listen_callback(self, source, condition):
        """
        Whenever a socket is written to, this callback handles the
        message. If it is a bounceback from this user, just drop the
        message. Otherwise check the 'action' to figure out what to
        do.
        """
        msg, (addr, port) = source.recvfrom(1024*4)
        m = json.loads(msg)
        for doc in self.documents:
            if doc.get_user() == m['user']:
                return
        action = m['action']
        if action == 'announce':
            self.recieve_announce(m, addr, port)
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
        if action == 'request_history':
            self.send_history(m)
        if action == 'send_history':
            self.recieve_history(m)

        return True

    def recieve_announce(self, m, addr, port):
        self.add_connection(m, addr, port)
        self.invite_to_document(m['user'], self.documents[0].get_user(),
                                self.documents[0].get_id())

        
    def send_snapshot(self, m):
        """
        Send the current snapshot of a document to a collaborator
        requesting it. Need to include the dependency id for it.
        """
        doc = self.get_document(m['doc_id'])
        deps = doc.get_last_changeset()
        deps = deps.to_dict() if deps else None
        msg = {'action': 'send_snapshot',
               'doc_id': doc.get_id(),
               'user': doc.get_user(),
               'snapshot': doc.get_snapshot(),
               'deps': deps}
        self.broadcast(msg)

    def recieve_snapshot(self, m):
        """
        Set a document snapshot from the one send from a collaborator.
        """
        doc = self.get_document(m['doc_id'])
        deps = m['deps']
        last_known_cs = doc.get_last_changeset()
        new_cs = self.build_changeset_from_dict(deps) if deps else None
        doc.set_snapshot(m['snapshot'], new_cs)
        if deps:
            self.request_history(doc, new_cs, last_known_cs)
        for callback in self.signal_callbacks['recieve-snapshot']:
            callback()

    def request_history(self, doc, new_cs, last_known_cs):
        """
        Request full info for changsets that have been referenced by are
        unknown to this collaborator. Also must send out the last
        changeset locally known so collborators know how much history
        to send. The local user wants all changesets from the
        last_known_cs up to the new_cs.
        """
        
        msg = {'action': 'request_history',
               'doc_id': doc.get_id(),
               'user': doc.get_user(),
               'new_cs_id':new_cs.get_id() if new_cs else None,
               'last_known_cs_id': last_known_cs.get_id() if last_known_cs else None
               }
        self.broadcast(msg)

    def send_history(self, m):
        """
        send the history to from last_known_cs to new_cs
        """
        doc = self.get_document(m['doc_id'])
        if not doc:
            return
        css = doc.get_changesets_in_range(m['last_known_cs_id'],
                                          m['new_cs_id'])
        msg = {'action': 'send_history',
               'doc_id': doc.get_id(),
               'user': doc.get_user(),
               'history': [cs.to_dict() for cs in css]
               }
        self.broadcast(msg)

    def recieve_history(self, m):
        """
        Get a list of past changesets and insert them into the
        document. Opperational transformation does not need to be done
        on these now. It is assumed that current snapshot already
        incorporates these changes.
        """
        doc = self.get_document(m['doc_id'])
        if not doc:
            return
        for cs in m['history']:
            # build historical changeset
            hcs = self.build_changeset_from_dict(cs)
            doc.insert_historical_changeset(hcs)
        
    def accept_invitation_to_document(self, m):
        """
        Accept an inviation to work on a document by requesting it's
        snapshot.
        """
        doc = self.new_document(m['doc_id'])
        self.request_snapshot(m['doc_id'])
        for callback in self.signal_callbacks['accept-invitation']:
            callback(doc)
    
    def request_snapshot(self, doc_id):
        """
        Request a document snapshot from a user.
        """
        doc = self.get_document(doc_id)
        msg = {'action':'request_snapshot',
               'user': doc.get_user(),
               'doc_id': doc_id}
        self.broadcast(msg)

        
    def update_cursor(self, msg):
        """
        Update the cursor position of a remote collaborator.
        """
        for c in self.connections:
            if c.user == msg['user']:
                if c.cursor['stamp'] < msg['cursor']['stamp']:
                    c.cursor = msg['cursor']
                break
        for callback in self.signal_callbacks['remote-cursor-update']:
            callback()
            
    def announce(self):
        """
        Builds message for announcing avalibility
        """
        msg = {'action':'announce',
               'user':self.default_user}
        self.broadcast(msg)

    def invite_to_document(self, to_user, from_user, doc_id):
        """
        Builds a message to invite another user to collaborate on a
        document.
        TODO: set from_user to defualt_user
        """
        msg = {"action":"invite_to_document",
               "to_user":to_user,
               "user":from_user,
               "doc_id":doc_id}
        self.broadcast(msg)
        
    def broadcast(self, msg):
        """
        BIG FUCKING TODO: fix connecions clas to handle all this
        """
        ports = [DEFAULT_COLLABORATOR_PORT]
        for c in self.connections:
            if not c.port in ports: port.append(c.port)
        for port in ports:
            self.s.sendto(json.dumps(msg), (HOST, port))

    
    def build_changeset_from_dict(self, m):
        """
        From a dict, build a changeset object with all its ops.
        TODO should not be in Collaborator class
        """
        doc = self.get_document(m['doc_id'])
        if not doc:
            return

        p = m # used to send whole message. fix this later TODO
        dependency = doc.get_changeset_by_id(p['dep_id'])
        dependency = p['dep_id'] if dependency == None else dependency
        cs = Changeset(p['doc_id'], p['user'], dependency)
        for j in p['ops']:
            op = Op(j['action'],j['path'],j['val'],j['offset'])
            cs.add_op(op)
        return cs
            
    def add_connection(self, m, addr, port):
        """
        TODO: point this to connection objects
        """
        for c in self.connections:
            if c.user == m['user']:
                c.update(addr, port)
                #c.send('known')
                return

        c = Connection(m['user'], addr, port)
        self.connections.append(c)
        c.send('learned');
        
    def connect(self, signal, callback):
        """
        Let clients connect to Collaborator by defining callbacks for
        various signals.
        """
        self.signal_callbacks[signal].append(callback)

    def recieve_changeset(self, m):
        """
        Handler for recieving changest messages from remote
        collaborators.
        """
        doc = self.get_document(m['doc_id'])
        if not doc:
            return

        cs = self.build_changeset_from_dict(m['payload'])
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

    
