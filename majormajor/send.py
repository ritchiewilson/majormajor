
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

import socket
import json



HOST = '<broadcast>'
PORT = 8000


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
s.connect((HOST, PORT))


msg ={'action':'changeset',
      'payload': [
          {'user':'not ritchie'},
          {'doc_id':'lorum ipsum'},
          {'deps':'lorum ipsum'},
          {'ops':[{'action':'si', 'path':[], 'val':'XYX', 'offset':2}]}
          ],
        'cs_id':'asldfka;sdlfa;sdlf'
}

cursor = {'action':'cursor',
          'cursor': {
              'path': [],
              'offset': 6,
              'stamp':9,
              },
          'user':'not ritchie',
          }

announce = {'action':'announce',
            'users': 'not ritchie',
            'doc_id': 'dummy'}

#s.send(json.dumps(announce))
s.send(json.dumps(msg))
#s.send(json.dumps(cursor))

s.close()
