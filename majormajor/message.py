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

import copy
import uuid
import json


class Message:
    def __init__(self, action=None, from_user=None, to_user=None, conns=None,
                 doc_id=None, doc=None,
                 cs_dicts=None, request_css=None, send_css=None,
                 sent_css=None, synced=True, request_ancestors=False,
                 msg=None):
        self.action = action
        self.from_user = from_user
        self.to_user = to_user
        self.conns = conns
        self.request_css = request_css
        self.doc = doc
        self.doc_id = doc_id
        self.request_css = request_css
        self.send_css = send_css
        self.sent_css = sent_css
        self.synced = synced
        self.request_ancestors = request_ancestors
        self.complete_dict = None
        if not action is None:
            self.collect_data()
        if not msg is None:
            self.complete_dict = msg
            self.parse_msg(msg)

    def get_action(self):
        return self.action

    def collect_data(self):
        if self.action == 'sync':
            self.deps = self.doc.get_dependencies()
        if self.action == 'send_snapshot':
            self.snapshot = copy.copy(self.doc.get_snapshot())
            self.deps = self.doc.get_dependencies()
            self.root_changeset = self.doc.get_root_changeset()
        if self.action == 'request_history':
            deps = self.doc.get_dependencies()
            self.new_cs_ids = [cs.get_id() for cs in deps]
            self.last_known_cs_ids = []
        if self.action == 'request_changesets':
            self.deps = self.doc.get_dependencies()

    def parse_msg(self, msg):
        self.action = msg['action']
        self.from_user = uuid.UUID(msg['from_user'])
        if not self.action in ['announce']:
            self.doc_id = uuid.UUID(msg['doc_id'])
        if self.action == 'sync':
            self.synced = msg['synced']
            self.request_css = msg['request_css']
            self.sent_cs_dicts = msg['send_css']
            self.dep_ids = msg['dep_ids']
        if self.action == 'send_snapshot':
            self.snapshot = msg['snapshot']
            self.dep_dicts = msg['deps']
            self.root_changeset_dict = msg['root']
        if self.action == 'request_history':
            self.new_cs_ids = msg['new_cs_ids']
            self.last_known_cs_ids = msg['last_known_cs_ids']
        if self.action == 'send_history':
            self.sent_cs_dicts = msg['send_css']
        if self.action == 'announce':
            self.conns = msg['conns']
        if self.action == 'invite_to_document':
            self.to_user = uuid.UUID(msg['to_user'])
        if self.action == 'request_changesets':
            self.request_css = msg['request_css']
            self.dep_ids = msg['dep_ids']
            self.request_ancestors = msg['request_ancestors']
        if self.action == 'send_changesets':
            self.sent_cs_dicts = msg['send_css']

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        if not self.complete_dict is None:
            return self.complete_dict
        msg = {'action': self.action,
               'from_user': self.from_user}
        if not self.action in ['announce']:
            msg['doc_id'] = str(self.doc.get_id())
        if self.action == 'sync':
            msg['synced'] = self.synced
            msg['request_css'] = self.request_css
            msg['send_css'] = [cs.to_dict() for cs in self.send_css]
            msg['dep_ids'] = [dep.get_id() for dep in self.deps]
        if self.action == 'send_snapshot':
            msg['snapshot'] = self.snapshot
            msg['deps'] = [dep.to_dict() for dep in self.deps]
            msg['root'] = self.root_changeset.to_dict()
        if self.action == 'request_history':
            msg['new_cs_ids'] = self.new_cs_ids
            msg['last_known_cs_ids'] = self.last_known_cs_ids
        if self.action == 'send_history':
            msg['send_css'] = [cs.to_dict() for cs in self.send_css]
        if self.action == 'announce':
            msg['conns'] = self.conns
        if self.action == 'invite_to_document':
            msg['to_user'] = str(self.to_user.get_id())
        if self.action == 'request_changesets':
            msg['request_css'] = self.request_css
            msg['dep_ids'] = [dep.get_id() for dep in self.deps]
            msg['request_ancestors'] = self.request_ancestors
        if self.action == 'send_changesets':
            msg['send_css'] = [cs.to_dict() for cs in self.send_css]

        return msg
