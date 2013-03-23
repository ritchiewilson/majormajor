import socket
import json



HOST = ''
PORT = 50007


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect((HOST, PORT))


msg = {'action':'changesets',
       'payload':[
           {
               'user':'not ritchie',
               'doc_id':'lorum ipsum',
               'deps':'lorum ipsum',
               'ops':[{'action':'si', 'path':[], 'val':'XX', 'offset':2}]
               }
               ]
}

s.send(json.dumps(msg))


s.close()
