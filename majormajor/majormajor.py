
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
from user import User
from ops.op import Op
import socket, copy, difflib
import json
import sys
import uuid
from datetime import datetime
import random

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
        self.remote_users = {}
        self.requested_changesets = {}

        # When used as a plugin, this should be tied into an event
        # loop. Currently GObject is hardcoded in. For testing, there is no
        # event loop so HAS_EVENT_LOOP needs to be manually set to False.
        self.HAS_EVENT_LOOP = True
        GObject.timeout_add(500, self.pull_from_pending_lists)
        GObject.timeout_add(2000, self._retry_request_changesets)
        GObject.timeout_add(5000, self._sync_documents)
        self.big_insert = False
        self.drop_random_css = False

    def open_default_connection(self, port):
        """
        Hard coded hack for testing purposes. Default connection is
        sending json by broadcasting UDP over the local network.
        """
        from connections.UDP import UDPBroadcastConnection
        c = UDPBroadcastConnection(callback=self._listen_callback,
                                   listen_port=port)
        self.connections.append(c)

    def open_mq_connection(self):
        from connections.MQ import RabbitMQConnection
        c = RabbitMQConnection(callback=self._listen_callback)
        self.connections.append(c)

    def pull_from_pending_lists(self):
        for doc in self.documents:
            old_state = copy.deepcopy(doc.get_snapshot())
            was_changed = doc.pull_from_pending_list()
            if was_changed:
                opcodes = doc.get_diff_opcode(old_state)
                for callback in self.signal_callbacks['receive-changeset']:
                    callback(opcodes)

            css = doc.get_send_queue()
            if css:
                self.send_changesets(doc=doc, css=css)
                doc.clear_send_queue()
        return True
            
    def new_document(self, doc_id=None, user=None, snapshot=None):
        """
        Create a new Document to add to the list of open
        documents. When no doc_id is provided, a random one will be
        assigned. When no user is defined, the default is used.
        TODO: should split this up into new_document and open_document
        """
        if user is None:
            user = self.default_user
        d = Document(doc_id, user, snapshot)
        if not self.HAS_EVENT_LOOP:
            d.HAS_EVENT_LOOP = False
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

    def send_changeset(self, cs):
        """
        Build the message object to send to other collaborators.
        """
        msg = {'action':'send_changeset',
               'cs':cs.to_dict(),
               'cs_id': cs.get_id(),
               'user':cs.get_user(),
               'doc_id':cs.get_doc_id()}
        self.broadcast(msg, broadcast=True)
        return msg

    def _listen_callback(self, msg):
        """
        Whenever a socket is written to, this callback handles the
        message. If it is a bounceback from this user, just drop the
        message. Otherwise check the 'action' to figure out what to
        do.
        """

        m = msg

        return_msg = {}

        if not 'action' in msg:
            return return_msg
            
        action = m['action']
        if action == 'announce':
            return_msg = self.receive_announce(m)
        if action == 'send_changeset':
            return_msg = self.receive_changeset(m)
        if action == 'send_changesets':
            return_msg = self.receive_changesets(m)
        if action == 'invite_to_document':
            return_msg = self.accept_invitation_to_document(m)
        if action == 'request_snapshot':
            return_msg = self.send_snapshot(m)
        if action == 'send_snapshot':
            return_msg = self.receive_snapshot(m)
        if action == 'request_history':
            return_msg = self.send_history(m)
        if action == 'send_history':
            return_msg = self.receive_history(m)
        if action == 'request_changesets':
            return_msg = self.respond_to_changeset_request(m)
        if action == 'sync':
            return_msg = self._sync_document(m)

        return return_msg

    def _retry_request_changesets(self):
        msg = {}
        for doc_id, css in self.requested_changesets.items():
            doc = self.get_document_by_id(doc_id)
            if not doc: continue
            missing_changesets = doc.get_missing_changeset_ids()
            request_list = []
            doc_dict = self.requested_changesets[doc_id]
            for cs_id, count in css.items():
                if not cs_id in missing_changesets:
                    del doc_dict[cs_id]
                elif count['countdown'] == 0:
                    request_list.append(cs_id)
                    doc_dict[cs_id]['countdown'] = count['next_start']
                    doc_dict[cs_id]['next_start'] = count['next_start'] * 2
                else:
                    doc_dict[cs_id]['countdown'] -= 1
            msg = self.request_changesets(doc, request_list, broadcast=True)
        if self.HAS_EVENT_LOOP:
            return True
        return msg

    def _sync_documents(self):
        """
        This is periodically called on a timer to check that documents are
        synced. If the Document has just recently received a new
        changeset, don't try to sync since it is probably already in
        process.
        """
        msg = {}
        for doc in self.documents:
            time_diff = datetime.now() - doc.get_time_of_last_received_cs()
            if time_diff.seconds < 5: continue
            self._sync_document(doc=doc)
        if self.HAS_EVENT_LOOP:
            return True
        return msg

    def _sync_document(self, msg=None, doc=None, user=None):
        if self.drop_random_css:
            return
        if doc is None:
            doc_id = msg['doc_id']
            doc = self.get_document_by_id(doc_id)
        if not doc:
            return
        # figure out who to send this message to
        users = []
        if msg:
            users = [self.get_user_by_id(uuid.UUID(msg['user']))]
        else:
            users = [u for u in self.remote_users.values()]
        if not users:
            return
        request_css, send_css = [], []
        synced = False
        if msg:
            # if there wasa message, and it was synced, quit
            if msg['synced'] is True:
                return

            # first accept any incoming changesets, collecting missing
            # changesets.
            user = self.get_user_by_id(uuid.UUID(msg['user']))
            r_css = {'css': msg['send_css']}
            self.receive_changesets(r_css, doc=doc, user=user)
            missing_cs_ids = self.update_missing_changesets(doc)

            # add to that any other missing deps
            _request_css, _send_css = doc.get_sync_status(msg['deps'])
            request_css = list(set(missing_cs_ids + _request_css))

            # get the rest of changesets to send
            send_local_dep_css = \
                    [doc.get_changeset_by_id(cs) \
                     for cs in msg['request_css'] if doc.knows_changeset(cs)]
            send_css = [cs.to_dict() \
                        for cs in list(set(send_local_dep_css + _send_css))]
            
            if not request_css and not send_css:
                synced = True
        deps = [dep.get_id() for dep in doc.get_dependencies()]
        msg = {'action': 'sync',
               'doc_id': doc.get_id(),
               'user': self.default_user,
               'synced': synced,
               'request_css': request_css,
               'send_css': send_css,
               'deps': deps}
        self.broadcast(msg, users=users)
        return msg

    def receive_announce(self, msg):
        if msg['user'] == self.default_user: return {}
        user_id = uuid.UUID(msg['user'])
        user = self.get_user_by_id(user_id)
        if user:
            user.add_connections(msg['conns'])
            return {}
        user = User(user_id)
        user.add_connections(msg['conns'])
        self.add_user(user)
        self.announce(users=[user])
        return {}

    def send_snapshot(self, m):
        """
        Send the current snapshot of a document to a collaborator
        requesting it. Need to include the dependency id for it.
        """
        doc = self.get_document_by_id(m['doc_id'])
        if not doc:
            return
        user = self.get_user_by_id(uuid.UUID(m['user']))
        deps = []
        for dep in doc.get_dependencies():
            deps.append(dep.to_dict())
        msg = {'action': 'send_snapshot',
               'doc_id': doc.get_id(),
               'user': self.default_user,
               'snapshot': doc.get_snapshot(),
               'deps': deps,
               'root': doc.get_root_changeset().to_dict()}
        self.broadcast(msg, users=[user])
        return msg

    def receive_snapshot(self, m):
        """
        Set a document snapshot from the one send from a collaborator.
        """
        doc = self.get_document_by_id(m['doc_id'])
        if not doc:
            return
        user = self.get_user_by_id(uuid.UUID(m['user']))
        last_known_deps = []
        doc.receive_snapshot(m)
        new_css = doc.get_dependencies()
        msg = {}
        if new_css:
            msg = self.request_history(doc, user, new_css, last_known_deps)
        for callback in self.signal_callbacks['receive-snapshot']:
            callback(doc.get_snapshot())
        return msg

    def request_history(self, doc, user, new_css, last_known_css):
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
        self.broadcast(msg, users=[user])
        return msg

    def send_history(self, m):
        """
        send the history to from last_known_cs to new_cs
        """
        doc = self.get_document_by_id(m['doc_id'])
        if not doc:
            return
        user = self.get_user_by_id(uuid.UUID(m['user']))
        css = doc.get_changesets_in_ranges(m['last_known_cs_ids'],
                                          m['new_cs_ids'])
        msg = {'action': 'send_history',
               'doc_id': doc.get_id(),
               'user': doc.get_user(),
               'history': [cs.to_dict() for cs in css]
               }
        self.broadcast(msg, users=[user])
        return msg

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
        doc = self.get_document_by_id(m['doc_id'])
        if doc:
            return
        doc = self.new_document(m['doc_id'])
        user = self.get_user_by_id(uuid.UUID(m['user']))
        msg = self.request_snapshot(doc, user)
        for callback in self.signal_callbacks['accept-invitation']:
            callback(doc)
        return msg
        
    def request_snapshot(self, doc, user):
        """
        Request a document snapshot from a user.
        """
        msg = {'action': 'request_snapshot',
               'user': self.default_user,
               'doc_id': doc.get_id()}
        self.broadcast(msg, users=[user])
        return msg

    def announce(self, users=[], broadcast=True):
        """
        Builds message for announcing avalibility
        """
        conns = [conn.get_listen_info() for conn in self.connections]
        msg = {'action': 'announce',
               'user': self.default_user,
               'conns': conns}
        self.broadcast(msg, users, broadcast)
        return msg

    def invite_all(self, doc):
        for user in self.remote_users.values():
            self.invite_to_document(doc, user)
            
    def invite_to_document(self, doc, to_user):
        """
        Builds a message to invite another user to collaborate on a
        document.
        TODO: set from_user to defualt_user
        """
        msg = {"action": "invite_to_document",
               "to_user": str(to_user.get_id()),
               "user": self.default_user,
               "doc_id": doc.get_id()}
        self.broadcast(msg, [to_user])
        return msg

    def request_changesets(self, doc, cs_ids, request_ancestors=False,
                           users=[], broadcast=False):
        if len(cs_ids) == 0:
            return {}
        if not doc:
            return
        msg = {"action": "request_changesets",
               "user": self.default_user,
               "doc_id": doc.get_id(),
               'cs_ids': cs_ids,
               "request_ancestors": request_ancestors}
        if request_ancestors:
            deps = doc.get_dependencies()
            msg['dependencies'] = [cs.get_id() for cs in deps]
            msg['number_of_known_css'] = len(doc.get_ordered_changesets())
        self.broadcast(msg, users=users, broadcast=broadcast)
        return msg

    def respond_to_changeset_request(self, m):
        doc = self.get_document_by_id(m['doc_id'])
        if not doc:
            return

        css = []
        if m['request_ancestors']:
            css = doc.request_ancestors(m['cs_ids'], m['dependencies'])
        else:
            css = [doc.get_changeset_by_id(cs) for cs in m['cs_ids']
                   if doc.knows_changeset(cs)]
        self.send_changesets(doc=doc, css=css)
            
    def send_changesets(self, m=None, doc=None, css=None):
        msg = {}
        doc = self.get_document_by_id(m['doc_id']) if not doc else doc
        if not doc:
            return
        css_data = None
        if css:
            css_data = [cs.to_dict() for cs in css]
        else:
            css_data = [doc.get_changeset_by_id(cs).to_dict() for cs in m['cs_ids'] \
                        if doc.knows_changeset(cs)]
        msg = {"action":"send_changesets",
               "user":self.default_user,
               "doc_id":doc.get_id(),
               'css':css_data}
        users = self.remote_users.values()
        self.broadcast(msg, users=users)
        return msg
        
    def broadcast(self, msg, users=[], broadcast=False):
        """
        msg is dict which contains all the information which should be
        broadcast to peers. Each connection is responsible for
        formatting the message how it wants and sending it out.
        """
        for c in self.connections:
            c.send(msg, users, broadcast)
            
    def connect(self, signal, callback):
        """
        Let clients connect to MajorMajor by defining callbacks for
        various signals.
        """
        self.signal_callbacks[signal].append(callback)

    def receive_changeset(self, m):
        m['css'] = [m['cs']]
        return self.receive_changesets(m)
    
    def receive_changesets(self, m, doc=None, user=None):
        """
        Handler for recieving changest messages from remote
        collaborators.
        """
        msg = {'one_inserted':False,
               'missing_dep_ids':[]}
        # For testing. If this flag is set, drop changesets at random
        # to simulate network problems.
        if self.drop_random_css and random.random() < 1:
            return msg
        if doc is None:
            doc_id = m['doc_id']
            doc = self.get_document_by_id(doc_id)
        if not doc:
            return
        if user is None:
            user = self.get_user_by_id(uuid.UUID(m['user']))

        doc.receive_changesets(m['css'])

        doc.time_of_last_received_cs = datetime.now()

        cs_ids = list(doc.get_missing_changeset_ids())
        msg = self.request_changesets(doc, cs_ids, request_ancestors=True,
                                      users=[user], broadcast=False)

        if not self.HAS_EVENT_LOOP:
            self.pull_from_pending_lists()
        
        return msg
            
    def update_missing_changesets(self, doc):
        if not doc in self.requested_changesets:
            self.requested_changesets[doc] = {}
        cs_ids = [cs_id for cs_id in doc.get_missing_changeset_ids()
                  if not cs_id in self.requested_changesets[doc]]
        for cs_id in cs_ids:
            self.requested_changesets[doc][cs_id] = {'countdown': 0,
                                                     'next_start': 1}
        return cs_ids

    def get_user_by_id(self, user_id):
        return self.remote_users.get(user_id, None)

    def add_user(self, user):
        if not user.get_id() in self.remote_users:
            self.remote_users[user.get_id()] = user

    def knows_user(self, user_id):
        return user_id in self.remote_users
        
    signal_callbacks = {
        'receive-changeset' : [],
        'receive-snapshot' : [],
        'remote-cursor-update' : [],
        'accept-invitation': [],
        }

