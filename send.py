import socket
import json



HOST = '<broadcast>'
PORT = 8080


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
s.connect((HOST, PORT))


msg = {'action':'changeset',
       'user':'not ritchie',
       'doc_id':'lorum ipsum',
       'deps':'lorum ipsum',
       'ops':[{'action':'si', 'path':[], 'val':'XYX', 'offset':2}]
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
            'user': 'not ritchie',
            'doc_id': 'dummy'}

#s.send(json.dumps(announce))
s.send(json.dumps(msg))
#s.send(json.dumps(cursor))

s.close()
