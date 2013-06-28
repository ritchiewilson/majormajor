
# MajorMajor - Collaborative Document Editing Library
# Copyright (C) 2013 Ritchie Wilson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from document import Document
from changeset import Changeset
from connection import Connection
from op import Op
import socket, copy, difflib
import json
import sys
import uuid
import datetime

from gi.repository import GObject


class MajorMajor:
    # TODO: user authentication

    def __init__(self):
        """
        On creation, create a socket to listen to UDP broadcasts on a
        default port.
        TODO: change this to a "connection" abstracion
        """
        self.documents = []
        self.connections = []
        self.default_user = str(uuid.uuid4())

        GObject.timeout_add(20, self.test_thousands_ops)
        GObject.timeout_add(500, self.close_open_changesets)
        self.big_insert = False


    def test_thousands_ops(self):
        if self.big_insert:
            doc = self.documents[0]
            import random, string
            n = random.randint(1,5)
            o = random.randint(0, len(doc.get_snapshot()))
            if random.random() > .3 or len(doc.get_snapshot()) == 0:
                l = unicode(''.join(random.choice(string.ascii_letters + string.digits)
                                    for x in range(n)))
                
                doc.add_local_op(Op('si',[],offset=o,val=l))
            else:
                while o + n > len(doc.get_snapshot()):
                    n -= 1
                if o == len(doc.get_snapshot()):
                    o -= 1
                    n = 1
                doc.add_local_op(Op('sd',[],offset=0,val=n))
                
            cs = doc.close_changeset()
            self.send_changeset(cs)
            for callback in self.signal_callbacks['receive-snapshot']:
                callback(doc.get_snapshot())
        return True

    def open_default_connection(self, port):
        """
        Hard coded hack for testing purposes. Default connection is
        sending json by broadcasting UDP over the local network.
        """
        from connections.UDP import UDPBroadcastConnection
        c = UDPBroadcastConnection(callback=self._listen_callback, listen_port=port)
        self.connections.append(c)
        
        
    def close_open_changesets(self):
        for doc in self.documents:
            for cs in doc.send_queue:
                self.send_changeset(cs)
            doc.clear_send_queue()
            oc = doc.get_open_changeset()
            if oc and not oc.is_empty():
                cs = doc.close_changeset()
                self.send_changeset(cs)
        return True

    def new_document(self, doc_id=None, user=None, snapshot=None):
        """
        Create a new Document to add to the list of open
        documents. When no doc_id is provided, a random one will be
        assigned. When no user is defined, the default is used.
        TODO: should split this up into new_document and open_document
        """
        if user == None:
            user = self.default_user
        d = Document(doc_id, user, snapshot)
        self.documents.append(d)
        return d

    def get_document_by_id(self, doc_id):
        """
        A MajorMajor can hold multiple documents. Get the relevent
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
        
    def _listen_callback(self, msg):
        """
        Whenever a socket is written to, this callback handles the
        message. If it is a bounceback from this user, just drop the
        message. Otherwise check the 'action' to figure out what to
        do.
        """

        m = msg

        action = m['action']
        if action == 'announce':
            self.receive_announce(m)
        if action == 'changeset':
            self.receive_changeset(m)
        if action == 'cursor':
            self.update_cursor(m)
        if action == 'invite_to_document':
            self.accept_invitation_to_document(m)
        if action == 'request_snapshot':
            self.send_snapshot(m)
        if action == 'send_snapshot':
            self.receive_snapshot(m)
        if action == 'request_history':
            self.send_history(m)
        if action == 'send_history':
            self.receive_history(m)
        if action == 'request_changesets':
            self.send_changesets(m)

        return True

    def receive_announce(self, m):
        self.invite_to_document(m['user'], self.documents[0].get_user(),
                                self.documents[0].get_id())

        
    def send_snapshot(self, m):
        """
        Send the current snapshot of a document to a collaborator
        requesting it. Need to include the dependency id for it.
        """
        doc = self.get_document_by_id(m['doc_id'])
        deps = []
        for dep in doc.get_dependencies():
            deps.append(dep.to_dict())
        msg = {'action': 'send_snapshot',
               'doc_id': doc.get_id(),
               'user': doc.get_user(),
               'snapshot': doc.get_snapshot(),
               'deps': deps,
               'root':doc.get_root_changeset().to_dict()}
        self.broadcast(msg)

    def receive_snapshot(self, m):
        """
        Set a document snapshot from the one send from a collaborator.
        """
        doc = self.get_document_by_id(m['doc_id'])
        if not doc:
            return
        last_known_deps = []
        doc.receive_snapshot(m)
        new_css = doc.get_dependencies()
        if new_css:
            self.request_history(doc, new_css, last_known_deps)
        for callback in self.signal_callbacks['receive-snapshot']:
            callback(doc.get_snapshot())

    def request_history(self, doc, new_css, last_known_css):
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
               'new_cs_ids': [cs.get_id() for cs in new_css ],
               'last_known_cs_ids': [cs.get_id() for cs in last_known_css]
               }
        self.broadcast(msg)

    def send_history(self, m):
        """
        send the history to from last_known_cs to new_cs
        """
        doc = self.get_document_by_id(m['doc_id'])
        if not doc:
            return
        css = doc.get_changesets_in_ranges(m['last_known_cs_ids'],
                                          m['new_cs_ids'])
        msg = {'action': 'send_history',
               'doc_id': doc.get_id(),
               'user': doc.get_user(),
               'history': [cs.to_dict() for cs in css]
               }
        self.broadcast(msg)

    def receive_history(self, m):
        """
        Get a list of past changesets and insert them into the
        document. Opperational transformation does not need to be done
        on these now. It is assumed that current snapshot already
        incorporates these changes.
        """
        doc = self.get_document_by_id(m['doc_id'])
        if not doc:
            return
        doc.receive_history(m)

        
    def accept_invitation_to_document(self, m):
        """
        Accept an inviation to work on a document by requesting it's
        snapshot.
        """
        doc = self.new_document(m['doc_id'])
        # TODO hardcoding this for testing
        self.documents = [doc]
        self.request_snapshot(m['doc_id'])
        for callback in self.signal_callbacks['accept-invitation']:
            callback(doc)
    
    def request_snapshot(self, doc_id):
        """
        Request a document snapshot from a user.
        """
        doc = self.get_document_by_id(doc_id)
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

    def request_changesets(self, doc_id, cs_ids):
        msg = {"action":"request_changesets",
               "user":self.default_user,
               "doc_id":doc_id,
               'cs_ids':cs_ids}
        self.broadcast(msg)

    def send_changesets(self, m):
        doc = self.get_document_by_id(m['doc_id'])
        if not doc:
            return
        for cs_id in m['cs_ids']:
            cs = doc.get_changeset_by_id(cs_id)
            self.send_changeset(cs)
        
    def broadcast(self, msg):
        """
        msg is dict which contains all the information which should be
        broadcast to peers. Each connection is responsible for
        formatting the message how it wants and sending it out.

        TODO: this will send out infor to eveyone, always. with better
        connections types, need methods to send information to only
        those who request it.
        """
        for c in self.connections:
            c.send(msg)
        
    def connect(self, signal, callback):
        """
        Let clients connect to MajorMajor by defining callbacks for
        various signals.
        """
        self.signal_callbacks[signal].append(callback)

    def receive_changeset(self, m):
        """
        Handler for recieving changest messages from remote
        collaborators.
        """
        doc = self.get_document_by_id(m['doc_id'])
        if not doc:
            return

        old_state = copy.deepcopy(doc.get_snapshot())
        if not doc.receive_changeset(m):
            return

        opcodes = doc.get_diff_opcode(old_state)

        for callback in self.signal_callbacks['receive-changeset']:
            callback(opcodes)

    signal_callbacks = {
        'receive-changeset' : [],
        'receive-snapshot' : [],
        'remote-cursor-update' : [],
        'accept-invitation': [],
        }

