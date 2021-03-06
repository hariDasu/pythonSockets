
#-----------------------------------------
#vi: sw=4 ts=4 expandtab nu
#-----------------------------------------

import socket               # Import socket module
import json
#import pdb, ipdb, pudb
#import PrettyPrinter
 


#----------------------------------------
clientSockArr={}

''' {to:[from, interface, cost],
     to:[from, interface, cost]
    }
     0 interface refers to local

     "N" (NaN) is a non-existant interface
'''
initialCostMatrix =   {

                        "0":[2,2,3],
                        "1":[2,0,1],
                        "2":[2,0,0],
                        "3":[1,"N",9999]

                };


rvcdRouteTable = [
                    ];

def  acceptOneConnection() :
    lsock = socket.socket()         # Create a socket object
    host2= '10.0.1.23'     # Get  machine name
    port = 16002
    lsock.bind((host2, port))        # Bind to the port
    lsock.listen(5)                 # Now wait for client connection.
    # lsock - blocking for conn
    csock, addr = lsock.accept()        # Establish connection with client.
    #  csock - turned to non-blocking
    #csock.setblocking(0)
    clientSockArr[addr]=csock
    print('Remembering  client socket from', addr)
    return csock

#----------------------------------------
def  readClientData(csock) :
    sentence=csock.recv(1024)
    return  sentence.upper().decode()

#----------------------------------------

def sendTable(clientSock) :
        toClientMsg = json.dumps(initialCostMatrix);
        clientSock.send(toClientMsg.encode());
#------------------------------------------
def bellmanFording(someTable,otherTable) :
    myNumber = someTable["0"][0];

    otherNumber = otherTable["0"][0];
    costTo = someTable[str(otherNumber)][2];
    intfTo = someTable[str(otherNumber)][1];

    for toRouter in someTable:
        #uI = unicode(i)
        uI = str(toRouter);
        #pudb.set_trace();

        replCost = otherTable[uI][2]+costTo;
        replIntf = otherTable[uI][1];

        if someTable[toRouter][2]>otherTable[uI][2]+costTo :
            someTable[toRouter][2]=replCost;
            someTable[toRouter][1]=intfTo;
#------------------------------------------

if __name__ == "__main__" :
    csock=acceptOneConnection()
    while True  :

        clientData=readClientData(csock)
        #print(clientData)
        rcvdRouteTable=json.loads(clientData)
        print(rcvdRouteTable);
        #print("hit enter to send to client...");
        #input();
        sendTable(csock);
        bellmanFording(initialCostMatrix,rcvdRouteTable)
        print(initialCostMatrix);

        #csock.send(clientData)
        #if upperSent=="DONE" :
        break
    csock.close()
