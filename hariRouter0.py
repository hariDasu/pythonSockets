#!/usr/bin/env python2.7
#--------------------------------
# vi:  sw=4 ts=4 expandtab ruler  nu
#--------------------------------
from gevent import monkey
monkey.patch_all()
import socket, select, os, sys, pdb
import logging, logging.handlers, logging.config
import time
import threading

myHost = socket.gethostname()
logger=logging.getLogger()

"""
Each row in the array rerpresents one routers neighbors
Each column is encoded as ToRouter:Interface:Cost
"""
initialSetup = [
    [ "1:0:1", "2:1:3",  "3:2:7" ] ,     # router 0 neighbors  ( ToRouter:Interface:Cost)
    [ "0:1:1", "2:0:1" ],                # router 1 neighbors
    [ "0:2:3", "1:0:1" , "3:1:2"],       # router 2 neighbors
    [ "0:0:7", "2:2:2"]                  # router 3 neighbors
]


"""
The RouteServer class listens to other router connect requests 
It spawns a RouteUpdater thread for each incoming connection 

"""

class RouteServer(threading.Thread):

    def __init__(self, threadID, name, routerNum=0, serverPort=5150):
        threading.Thread.__init__(self)    # init super class 
        self.threadID = threadID           #  
        self.name = name                   # human name to id this thread
        self.srvrPort=serverPort;          # server port
        self.serverSock=None;              # our listening   socket
        self.inCntr=0                      # counter for incoming connects
        self.routerNum=routerNum
        self.dvrTable= {"0": [0, 0, 0],
                        "1": [0, 1, 1],
                        "2": [0, 2, 3],
                        "3": [0, 3, 7]
        }
        #---------
        self.inClients={};                 # keeps track of incoming clients
        self.outConnects={};               # keeps track of outgoing connections
        self.updateDVRtable(newValues=None)

    #----------------------------------------------
    def updateDVRtable(self, newValues={} ) :
        if newValues==None:
            #update  from  initialSetup  (based on self.routerNum )
            logger.info ("Initializing Router-%d DVRT from static values .." % (self.routerNum) )
            pass
        else :
            logger.info ("Initializing DVRT from remote router ..")

            #update from the json we got from remote router
            pass

    #-----------------------------------------------
    # a server listens to incoming client connections
    def setupListener(self):
        self.serverSock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #self.serverSock.setblocking(0)
        self.serverSock.bind(("localhost",self.srvrPort));
        self.serverSock.listen(5)
        self.msgInCnt=0
        logger.info("Listen on port: %d" %(self.srvrPort))

    #------------------------------------------------
    def acceptClientConnection(self) :
        try :
            incSock, address = self.serverSock.accept()
            clientAddr = "%s:%s" % (address)
            logger.info("Conection from : %s" % (clientAddr))
            self.inCntr+=1
            newClient = RouteUpdater( self.inCntr, "Thread-%d" % self.inCntr, self,  incSock )
            self.inClients[clientAddr]=newClient
            newClient.start()
        except Exception,e :
            print(e)


    #-----------------------------------------------
    def run(self):
        logger.info("Starting " + self.name)
        self.setupListener()
        while True :
            self.acceptClientConnection()
            time.sleep(1)

#============================================
"""
RouteUpdater class is a thread spawned from RouteServer for each incoming connection
It takes the updated tables from the connected client
and calls the updateDVRtable method on  RouteServer
"""
class RouteUpdater(threading.Thread) :
    def __init__(self, threadID, name, routeServer, incSocket) :
        threading.Thread.__init__(self)    # init super class 
        self.mySock=incSocket
        self.rtServer=routeServer

    #-----------------------------------------------
    def processRequest(self, req) :
        logger.info ("Req : %s" % req )
        self.mySock.send("Hello: %s" % req)      # echo back .. (for testing only)
        self.rtServer.updateDVRtable(resp)
        # take the latest DVRT from RoutePublisher (client) and udate
        # the DVR table on our routeServer

    #-----------------------------------------------
    def run(self):
        logger.info("Starting " + self.name)
        while True :
            req = self.mySock.recv(2000)
            self.processRequest(req)

#============================================

"""
RoutePublisher class is a client which 
* intiates the connection request
* sends route table requests 
* recieves route table responses and updates the DVR table
* there is one of these per edge 
* the DVR table itself is maintained in the RouteServer object.
"""
class RoutePublisher (threading.Thread):
    def __init__(self, threadID, name, routeServer=None, toHost="localhost", toPort=5150) :
        threading.Thread.__init__(self)    # init super class 
        self.outSock=None
        self.toHost=toHost
        self.toPort=toPort
        self.rtServer=routeServer

    #------------------------------------------------
    def doConnectOut(self) :
        sockout = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #sockout.setblocking(0)
        logger.info("Connecting out to %s:%d" %(self.toHost,self.toPort))
        try :
            sockout.connect((self.toHost,self.toPort))
            self.outSock=sockout
        except Exception,e :
            logger.info("%s: Cannot connect to %s:%d" %(e,self.toHost,self.toPort))
            self.outSock=None
    #----------------------------------------------
    def run(self) :
        while True :
            if not self.outSock :
                self.doConnectOut()
            else :
                # publish our DVR table to the server we are connected to
                self.outSock.send("Publish DVR")
                resp=self.outSock.recv(1000)
                logger.info ("%s: Resp ->  %s" % (self.name, resp) )
            time.sleep(3)

#============================================
"""
Depending on which router insatance 
establish one connection (each edge) to another router
"""
def openOutgoingConnections() :
    pass

#==============================================

"""
Startup arguments 
arg1 => what is my router number
"""
if __name__  == "__main__"  :
    logging.config.fileConfig("log4py.conf")
    rtrNum=0
    if len(sys.argv) >  1:
        rtrNum=int(sys.argv[1])
    # Create new threads
    rtServer = RouteServer(1, "Listener-1", routerNum=rtrNum, serverPort=5150)
    client1 = RoutePublisher(2, "Out-1", routeServer=rtServer, toHost="localhost",  toPort=5150)
    rtServer.start()
    client1.start()
