#!/usr/bin/env python2.7
#--------------------------------
# vi:  sw=4 ts=4 expandtab ruler  nu
#--------------------------------
from gevent import monkey
monkey.patch_all()
import socket, select, os, sys, pdb
import logging, logging.handlers, logging.config
import time
import json,commands
import threading
from pprint import PrettyPrinter

pp= PrettyPrinter(indent=5)

myHost = socket.gethostname()
logger=logging.getLogger()

"""
Each row in the array rerpresents one routers neighbors
Each column is encoded as ToRouter:Interface:Cost
"""
initialRoutes = [
    [ "0:0:0", "1:0:1", "2:1:3",  "3:2:7" ] ,     # router 0 neighbors  ( ToRouter:Interface:Cost)
    [ "0:1:1", "1:0:0", "2:0:1","3:9999:9999" ],                # router 1 neighbors
    [ "0:2:3", "1:0:1" , "2:0:0", "3:1:2"],       # router 2 neighbors
    [ "0:0:7", "1:9999:9999", "2:2:2", "3:0:0"]                  # router 3 neighbors
]

"""
routerSetup=[
    ("10.0.1.24" , 5150),  #iMac
    ("10.0.1.32" , 5151),  #mbpR
    ("10.0.1.23" , 5152),  #linuxMint
    ("10.0.1.24" , 5153)   #iMac2
]
"""

routerSetup=[
    ("localhost" , 5150),  #iMac
    ("localhost" , 5151),  #mbpR
    ("localhost" , 5152),  #linuxMint
    ("localhost" , 5153)   #iMac2
]
 



def tinit() :
    global  rtr1,rtr2, rtr3, rtr4, _nm
    _bGra="[40m"
    _bRed="[41m"
    _bGre="[42m"
    _bYel="[43m"
    _bBlu="[44m"
    _bPur="[45m"
    _bCya="[46m"
    _bWhi="[47m"
    _fBlk="[0;30m"
    _fRed="[0;31m"
    _fGre="[0;32m"
    _fYel="[0;33m"
    _fBlu="[0;34m"
    _fPur="[0;35m"
    _fCya="[0;36m"
    _fWhi="[0;37m"
    _nm="[m"
    os.environ['TERM']='ansi'
    _bd=commands.getoutput("tput smso")
    _cls=commands.getoutput("tput clear")
    _invis=commands.getoutput("tput invis")
    _ul=commands.getoutput("tput ul")
    _em=commands.getoutput("tput bold")
    rtr1="%s%s" % (_bGra, _fRed)
    rtr2="%s%s" % (_bGra, _fGre)
    rtr3="%s%s" % (_bGra, _fBlu)
    rtr4="%s%s" % (_bGra, _fYel)

#-----------------------------------------------------
def  thrdLog( rtrNum, msg) :
    prefix=(rtr1, rtr2, rtr3, rtr4)
    pref=rtrNum % len(prefix)
    logger.info ("%sROUTER %d%s %s" % (prefix[pref], rtrNum , _nm,  msg) )

#-----------------------------------------------------
"""
The RouteServer class listens to other router connect requests 
It spawns a RouteUpdater thread for each incoming connection 

"""

class RouteServer(threading.Thread):

    def __init__(self, threadID, name, routerNum=0 ) :
        threading.Thread.__init__(self)    # init super class 
        self.threadID = threadID           #  
        self.name = name                   # human name to id this thread
        self.serverSock=None;              # our listening   socket
        self.inCntr=0                      # counter for incoming connects
        self.routerNum=routerNum
        self.srvrPort=routerSetup[routerNum][1]
        self.dvrTable= {
            #key :  (from, ,interface,  cost)
        }
        #---------
        self.inClients={};                 # keeps track of incoming clients
        self.outConnects={};               # keeps track of outgoing connections
        self.tableVersion=0
        self.updateDVRtable(remRouter=self.routerNum, newValues=None)

    #----------------------------------------------
    def updateDVRtable(self, remRouter=0, newValues={} ) :
        if newValues==None:
            #update  from  initialRoutes  (based on self.routerNum )
            thrdLog(self.routerNum,"Initializing Router-%d DVRT from static values .." % (self.routerNum) )
            myInitialCosts=initialRoutes[self.routerNum]
            for ric  in myInitialCosts :
                (toRouter, interface, cost) = ric.split(':')
                self.dvrTable[int(toRouter)]=(self.routerNum, int(interface), int(cost) )
            self.tableVersion+=1
        else :
            thrdLog(remRouter, "Updating DVRT from remote router routes ..")
            # update from the json we got from remote router 
            # bump up the version only if at least one row changed

        thrdLog(self.routerNum, "Router %d: Table Version %d " % (self.routerNum,  self.tableVersion ) )
        pp.pprint(self.dvrTable)

    #-----------------------------------------------
    # a server listens to incoming client connections
    def setupListener(self):
        self.serverSock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #self.serverSock.setblocking(0)
        self.serverSock.bind(("",self.srvrPort));
        self.serverSock.listen(5)
        self.msgInCnt=0
        thrdLog(self.routerNum, "Listen on port: %d" %(self.srvrPort))

    #------------------------------------------------
    def acceptClientConnection(self) :
        try :
            incSock, address = self.serverSock.accept()
            clientAddr = "%s:%s" % (address)
            thrdLog(self.routerNum, "Conection from : %s" % (clientAddr))
            self.inCntr+=1
            newClient = RouteUpdater( self.inCntr, "Thread-%d" % self.inCntr, self,  incSock )
            self.inClients[clientAddr]=newClient
            newClient.start()
        except Exception,e :
            print(e)


    #-----------------------------------------------
    def run(self):
        thrdLog(self.routerNum, "Starting " + self.name)
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
    def processRequest(self, remoteTable) :
        try :
            rcvdTable = json.loads(remoteTable)
            remRouter=int(rcvdTable['0'][0])
            thrdLog(remRouter, "Processing update from %d" % (remRouter) )
            pp.pprint(rcvdTable)
            self.rtServer.updateDVRtable(remRouter, rcvdTable)
            self.mySock.send("Hello: %s" % "ok")      # echo back .. (for testing only)
        except Exception,e :
            logger.error ('Lost connection from ...')
            self.mySock=None
        # take the latest DVRT from RoutePublisher (client) and udate
        # the DVR table on our routeServer

    #-----------------------------------------------
    def run(self):
        logger.info("Starting " + self.name)
        while self.mySock != None  :
            remTable = self.mySock.recv(2000)
            self.processRequest(remTable)

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
        self.routerNum=self.rtServer.routerNum
        self.lastPubVersion=None

    #------------------------------------------------
    def doConnectOut(self) :
        sockout = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #sockout.setblocking(0)
        thrdLog(self.routerNum, "Connecting out to %s:%d" %(self.toHost,self.toPort))
        try :
            sockout.connect((self.toHost,self.toPort))
            self.outSock=sockout
        except Exception,e :
            thrdLog(self.routerNum, "%s: Cannot connect to %s:%d" %(e,self.toHost,self.toPort))
            self.outSock=None
    #----------------------------------------------
    def run(self) :
        while True :
            if not self.outSock :
                self.doConnectOut()
            else :
                # publish our DVR table to the server we are connected to
                # only  if our table version changed
                if self.rtServer.tableVersion != self.lastPubVersion :
                    toMsg = json.dumps(self.rtServer.dvrTable);
                    self.outSock.send(toMsg)
                    resp=self.outSock.recv(1000)
                    self.lastPubVersion=self.rtServer.tableVersion
                    logger.info ("%s: Resp ->  %s" % (self.name, resp) )
            time.sleep(3)

#============================================
"""
Depending on which router instance 
establish one connection (each edge) to another router
"""
def openOutgoingConnections(routeServer, myRouterNum) :
    thrdLog( myRouterNum, "Opening outgoing connections for Router %d" % (myRouterNum) )
    myNeighbors=initialRoutes[myRouterNum]
    for neighborInfo in myNeighbors :
        (toRouter,interface, cost) = neighborInfo.split(':')
        #pdb.set_trace();
        if (cost=='0' or cost=='9999') :
            continue
        (toHost, toPort)=routerSetup[int(toRouter)]
        client1 = RoutePublisher(toRouter, "Out-%d" % (int(toRouter)), routeServer=routeServer, toHost=toHost, toPort=toPort)
        client1.start()

#==============================================

"""
Startup arguments 
arg1 => what is my router number
"""
if __name__  == "__main__"  :
    logging.config.fileConfig("log4py.conf")
    tinit()
    rtrNum=0
    if len(sys.argv) >  1:
        rtrNum=int(sys.argv[1])
    # Create new threads
    rtServer = RouteServer(1, "Listener-1", routerNum=rtrNum)
    rtServer.start()
    openOutgoingConnections(rtServer, rtrNum)
