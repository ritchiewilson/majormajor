
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

import json
import random

from gi.repository import GObject
import pika

from connection import Connection
from ..message import Message

class RabbitMQConnection(Connection):
    def __init__(self, callback=None):
        self.on_receive_callback = callback
        self._type = "rabbitmq"
        MM = 'majormajor'
        # connect to the global channels where messages are broadcasted
        writes = random.sample(xrange(4), 2)
        reads = [x for x in xrange(4) if not x in writes]
        self.global_write_queues = [MM + str(x) for x in writes]
        self.global_read_queues = [MM + str(x) for x in reads]
        connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        for x in xrange(4):
            q = MM + str(x)
            channel.queue_declare(queue=q)

        # set up a new queue where people can message this person directly.
        self.read_queue = False
        i = 0
        while self.read_queue is False:
            queue_name = MM + str(i)
            try:
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters('localhost'))
                channel = connection.channel()
                channel.queue_declare(queue=queue_name, passive=True)
            except:
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters('localhost'))
                self.channel = connection.channel()
                self.channel.queue_declare(queue=queue_name)
                self.read_queue = queue_name
            i += 1
        self.all_read_queues = [self.read_queue] + self.global_read_queues[:]
        GObject.timeout_add(100, self._check_for_messages)

    def get_type(self):
        return "rabbitmq"

    def _check_for_messages(self):
        for q in self.all_read_queues:
            method_frame, header_frame, body \
                = self.channel.basic_get(queue=q, no_ack=True)
            if body and not method_frame.NAME == 'Basic.GetEmpty':
                m = json.loads(body)
                msg = Message(msg=m)
                self.on_receive_callback(msg)
                break
        return True

    def get_listen_info(self):
        msg = {'conn_type': 'rabbitmq',
               'conn_data': {'read_queue': self.read_queue}}
        return msg

    def send(self, msg, users=[], broadcast=False):
        """
        If this gets a list of users, this figures out the best way to send the
        message to everyone. If no users are given, the message gets sent to
        everyone in this connection.
        """
        # get any specific users that can be reached
        q_list = [u.get_properties_for_connection(self._type)['read_queue']
                  for u in users if u.has_connection(self.get_type())]

        if broadcast:
            q_list += self.global_write_queues

        json_msg = msg.to_json()
        for q in q_list:
            self.channel.basic_publish(exchange='',
                                       routing_key=q,
                                       body=json_msg)
        return True
