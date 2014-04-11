#!/usr/bin/env  python2.7
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
                    0:[0, 0, 0],
                    1:[0, 1, 1],
                    2:[0, 2, 3],
                    3:[0, 3, 7]
                };
#----------------------------------------
def  readServerData(ssock)  :
    fromServer=ssock.recv(1024)
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


def bellmanFording(someTable,otherTable) :
    for i in range (len(someTable)):
        uI = unicode(i)
        myNumber = someTable[i][0];
        otherNumber = int(otherTable[uI][0]);
        costTo = someTable[otherNumber][2];
        intfTo = someTable[otherNumber][1];

        replCost = otherTable[uI][2]+costTo;
        replIntf = otherTable[uI][1];

        if someTable[i][2]>otherTable[uI][2]+costTo :
            someTable[i][2]=replCost;
            someTable[i][1]=intfTo;



#client
if __name__ == "__main__" :
    host = ''
    printRouteTable();
    serverSock=socket(AF_INET, SOCK_STREAM)
    serverSock.connect((host, 16001))
    
    while True :
        #msg2Server=input("Enter lower case text : " )
        # pdb.set_trace()
        #Sending route table to server
        toSend = json.dumps(costMatrix);
        serverSock.send(toSend);
        #Getting route table from server
        print("waiting for server data...");
        fromServer = json.loads(readServerData(serverSock))
        pp.pprint(fromServer);
        bellmanFording(costMatrix,fromServer);
        #printing updated routes table
        printRouteTable();
        


    

        
        break

