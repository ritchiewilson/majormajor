
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

from connection import Connection
import socket, json
from gi.repository import GObject


class UDPBroadcastConnection(Connection):
    host = '<broadcast>'

    def __init__(self, callback=None, listen_port=8080):
        self.on_receive_callback = callback
        self.listen_port = listen_port

        # list of tuples with ip and port
        self.remote_user_addresses = [(self.host, 8000)] 
        if self.listen_port == 8000:
            self.remote_user_addresses = [(self.host, 8080)] 
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.s.bind((self.host, listen_port))
        GObject.io_add_watch(self.s, GObject.IO_IN, self._listen_callback)


    def send(self, msg):
        msg = json.dumps(msg)
        for addr in self.remote_user_addresses:
            self.s.sendto(msg, (self.host, addr[1]))

    def _listen_callback(self, source, condition):
        msg, (addr, port) = source.recvfrom(1024*4)
        #if (addr, port) not in self.remote_user_addresses:
        #    self.remote_user_addresses.append((addr, port))
        m = json.loads(msg)
        self.on_receive_callback(m)
        return True
        

    
