#!/usr/bin/env  python2.7
#-----------------------------------------
#vi: sw=4 ts=4 expandtab nu
#-----------------------------------------

import socket               # Import socket module
import json
from pprint import PrettyPrinter


pp=PrettyPrinter(indent=4);
#----------------------------------------
clientSockArr={}

''' {to:[from, interface, cost],
     to:[from, interface, cost]
    }
     0 interface refers to local

     "N" (NaN) is a non-existant interface
'''
initialCostMatrix =   {
                        
                        0:[1,2,1],
                        1:[1,0,0],
                        2:[1,0,1],
                        3:[1,"N",9999]
                    
                };


rvcdRouteTable = [
                    ];

def  acceptOneConnection() :
    lsock = socket.socket()         # Create a socket object
    host = ''     # Get  machine name
    port = 16001
    lsock.bind((host, port))        # Bind to the port
    lsock.listen(5)                 # Now wait for client connection.
    # lsock - blocking for conn
    csock, addr = lsock.accept()        # Establish connection with client.
    #  csock - turned to non-blocking
    #csock.setblocking(0)
    clientSockArr[addr]=csock
    print( 'Remembering  client socket from', addr)
    return  csock

#----------------------------------------
def  readClientData(csock) :
    sentence=csock.recv(1024)
    return  sentence.upper().decode()

#----------------------------------------

def sendTable(clientSock) :
        toClientMsg = json.dumps(initialCostMatrix);
        clientSock.send(toClientMsg);        
#-----------------------------------------

if __name__ == "__main__" :
    csock=acceptOneConnection()
    while True  :

        clientData=readClientData(csock)
        #print(clientData)
        rcvdRouteTable=json.loads(clientData)
        pp.pprint(rcvdRouteTable);
        print("hit enter to send to client...");
        raw_input();
        sendTable(csock);
        bellmanFording(initialCostMatrix,rcvdRouteTable)
        pp.pprint(initialCostMatrix);

        #csock.send(clientData)
        #if upperSent=="DONE" :
        break
    csock.close()
