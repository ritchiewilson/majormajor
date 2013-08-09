
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
import socket, json, uuid
from datetime import datetime
from gi.repository import GObject
from collections import defaultdict

class UDPBroadcastConnection(Connection):
    host = '<broadcast>'

    def __init__(self, callback=None, listen_port=8080):
        self.on_receive_callback = callback
        self.listen_port = listen_port
        self.received_msg_chunks = {}
        # TODO: periodically clean received_msg_chunks of any messages
        # that probably just got dropped.

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
        """
        Using a simple UDP socket, this broadcasts the given message. For
        larger messages, split the raw json into 4000 character
        chunks.

        So it can be reassembled later, each chunk needs to be sent with
        a msg_id, chunk index, and the number of chunks in the full
        message, each seperated with a ":".

        <msg_id>:<index>:<number of chunks>:<json data>

        TODO: Messages should be split by bytes, not characters (unicode)
        
        """
        full_msg = json.dumps(msg)
        msg_id = str(uuid.uuid4())
        chunk_size = 1000
        chunks = [full_msg[i:i+chunk_size] \
                  for i in xrange(0, len(full_msg), chunk_size)]
        number_of_chunks = len(chunks)
        msg_chunks = []
        for i in xrange(number_of_chunks):
            chunk = "".join([msg_id, ":", str(i+1), ":", \
                             str(number_of_chunks), ":", chunks[i]])
            msg_chunks.append(chunk)
        for chunk in msg_chunks:
            for addr in self.remote_user_addresses:
                self.s.sendto(chunk, (self.host, addr[1]))

    def _listen_callback(self, source, condition):
        """
        When a message is received, split out the metadata and try to
        reassemble the original message. If a full message can be
        determined, pass it back to majormajor.
        """
        raw_data, (addr, port) = source.recvfrom(1024*4)
        # split out metadata from json
        msg_id, index, size, payload = raw_data.split(":", 3)
        full_msg = False
        if size == '1':
            # if this is the one and only chunk for this message,
            # don't bother storing an reloading.
            full_msg = payload
        else:
            self.store_msg_chunk(msg_id, int(index), int(size) ,payload)
            full_msg = self.get_complete_msg(msg_id)

        if full_msg:
            m = json.loads(full_msg)
            self.on_receive_callback(m)
            self.received_msg_chunks.pop(msg_id, None)
        return True

    def store_msg_chunk(self, msg_id, index, size, payload):
        """
        Store the incoming information in nested dicts. Incoming chunks
        are stored like this until they can all be reassembled.

        Args:
           msg_id (str): A common id for all chunks in the message
           index (int): The index of this chunk, 1 through size inclusive
           size (int): Total number of chunks in message
           payload (str): This chunk of JSON (not valid JSON)

        """
        if not msg_id in self.received_msg_chunks:
            self.received_msg_chunks[msg_id] = {'size': size,
                                                'chunks': {},
                                                'time': datetime.now()}
        chunks = self.received_msg_chunks[msg_id]['chunks']
        if not index in chunks:
            chunks[index] = payload

    def get_complete_msg(self, msg_id):
        """
        Reassemble the chunks of the json message associated with the
        given msg_id. If all of the peices are not yet known, return
        False.
        """
        msg_data = self.received_msg_chunks[msg_id]
        size = msg_data['size']
        chunks = msg_data['chunks']
        if size == len(chunks):
            return "".join([chunks[i] for i in xrange(1,size+1)])
        return False
