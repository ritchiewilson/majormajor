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

import uuid


class User:
    def __init__(self, _id=None):
        self._id = _id if _id else uuid.uuid4()
        self.documents = set([])
        self.connections = {}
        self.nickname = str(self._id)

    def add_document(self, doc):
        self.documents.update([doc])

    def add_connections(self, conns):
        for conn in conns:
            self.connections[conn['conn_type']] = conn['conn_data']

    def get_properties_for_connection(self, conn_type):
        return self.connections.get(conn_type, None)

    def has_connection(self, conn_type):
        return conn_type in self.connections

    def get_id(self):
        return self._id
