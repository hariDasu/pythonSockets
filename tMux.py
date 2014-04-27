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


class ListenerThread (threading.Thread):

    def __init__(self, threadID, name, serverPort=5150):
        threading.Thread.__init__(self)    # init super class 
        self.threadID = threadID           #  
        self.name = name                   # human name to id this thread
        self.srvrPort=serverPort;          # server port
        self.inClients={};                 # keeps track of incoming clients
        self.outConnects={};               # keeps track of outgoing connections
        self.serverSock=None;              # our listening   socket
        self.inCntr=0                      # counter for incoming connects

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
            newClient = InClientThread( self.inCntr, "Thread-%d" % self.inCntr, incSock )
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
class InClientThread(threading.Thread) :
    def __init__(self, threadID, name, incSocket) :
        threading.Thread.__init__(self)    # init super class 
        self.mySock=incSocket

    #-----------------------------------------------
    def processRequest(self, req) :
        logger.info ("Req : %s" % req )
        self.mySock.send("Hello: %s" % req)      # echo back ..

    #-----------------------------------------------
    def run(self):
        logger.info("Starting " + self.name)
        while True :
            req = self.mySock.recv(2000)
            self.processRequest(req)

#============================================

class ClientThread (threading.Thread):
    def __init__(self, threadID, name, toHost="localhost", toPort=5150) :
        threading.Thread.__init__(self)    # init super class 
        self.outSock=None
        self.toHost=toHost
        self.toPort=toPort

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
                # fetch remote data
                self.outSock.send("Fetch DVR")
                resp=self.outSock.recv(1000)
                logger.info ("%s: Resp ->  %s" % (self.name, resp) )
            time.sleep(3)


#============================================
if __name__  == "__main__"  :
    logging.config.fileConfig("log4py.conf")
    # Create new threads
    thread1 = ListenerThread(1, "Listener-1", serverPort=5150)
    thread2 = ClientThread(2, "Out-1", toHost="localhost",  toPort=5150)
    thread1.start()
    thread2.start()
