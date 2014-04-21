#!/usr/bin/env  py
#-----------------------------------------
#vi: sw=4 ts=4 expandtab nu
#-----------------------------------------
import pdb
import json
from pprint import PrettyPrinter
from socket import *   


pp=PrettyPrinter(indent=4);
''' {to:[from, interface, cost],
     to:[from, interface, cost]
    }
     0 interface refers to local
     "N" (NaN) is a non-existant interface
'''
costMatrix =   {
                    "0":[0, 0, 0],
                    "1":[0, 1, 1],
                    "2":[0, 2, 3],
                    "3":[0, 3, 7]
                };
#----------------------------------------
def  readServerData(ssock)  :
    fromServer=ssock.recv(1024).decode()
    return fromServer
#----------------------------------------

def printRouteTable() :
    for toRouter in costMatrix  :
        fromMessage = " From Router %s"%(costMatrix[toRouter][0])
        destMessage = " To Router %s"%(toRouter)
        intfMessage = " Over interface %s"%(costMatrix[toRouter][1])
        costMessage = " with Cost  %s"%(costMatrix[toRouter][2])
        #%s to router %s over interface %s has cost %s\n"%(costMatrix[0][i][0],costMatrix[0][i][1],costMatrix[0][i][2],costMatrix[0][i][3])
        print(fromMessage + destMessage + intfMessage + costMessage);

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


#client
if __name__ == "__main__" :
    host1 = '128.235.208.35'
    host2 = '128.235.211.21'
    host3 = ''

    printRouteTable();
    serverSock=socket(AF_INET, SOCK_STREAM)
    serverSock.connect((host1, 16001))
    serverSock.connect((host2, 16002))
    serverSock.connect((host3, 16003))
    while True :
        #msg2Server=input("Enter lower case text : " )
        # pdb.set_trace()
        #Sending route table to server
        toSend = json.dumps(costMatrix);

        serverSock.send(toSend.encode());
        #Getting route table from server
        fromServer = json.loads(readServerData(serverSock))
        #nonBytes = fromServer.decode()
        pp.pprint(fromServer);
        bellmanFording(costMatrix,fromServer);
        #printing updated routes table
        printRouteTable();
        

        
        break

