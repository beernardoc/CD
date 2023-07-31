"""CD Chat client program"""
import datetime
import fcntl
import json
import logging
import os
import selectors
import sys
import socket

from .protocol import CDProto, CDProtoBadFormat, TextMessage
from .protocol import RegisterMessage

logging.basicConfig(filename=f"{sys.argv[0]}.log", level=logging.DEBUG)


class Client:
    """Chat Client process."""
    print("CHAT:\n")

  



    def __init__(self, name: str = "Foo"):
        """Initializes chat client."""
        print("BEM VINDO " + name + "\n")
        global nome
        nome = name
        global canal
        canal = None
       
              


        pass

    def connect(self):
        """Connect to chat server and setup stdin flags."""
        global sock
        global host
        global port
        global selec
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        selec = selectors.DefaultSelector()
        host = "localhost"
        port = 2000
        
        sock.connect((host,port))
        selec.register(sock,selectors.EVENT_READ,self.read)
        
       
        message = CDProto.register(nome)
        CDProto.send_msg(sock,message)
              

    def loop(self):
        """Loop indefinetely."""
        global selec
        global sock

        flag = fcntl.fcntl(sys.stdin,fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin,fcntl.F_SETFL, flag | os.O_NONBLOCK)

        selec.register(sys.stdin,selectors.EVENT_READ, self.keyboard)
        

        while True:
            sys.stdout.write("Escreva algo: ")
            sys.stdout.flush()
            events = selec.select()
            for key,mask in events:
                callback = key.data
                callback(key.fileobj,mask)

    def read(self,sock,mask):

        msg = CDProto.recv_msg(sock)
        
        if type(msg) is TextMessage:
            print("\n> " + msg.message + "\n")
        



    def keyboard(self,stdin,mask): #write
        global nome
        global sock
        global selec
        global canal
        line = stdin.read()



        now = datetime.datetime.now().timestamp()


        if "exit" in str(line): 
            print("SAINDO...")
            selec.unregister(sock)
            sock.close()
            sys.exit()

        elif "/join" in str(line):
            canal = str(line.split()[1])
            message = CDProto.join(canal)
            CDProto.send_msg(sock,message)
            print("você está no canal" + canal)



        elif "/register" in str(line): 
            message = CDProto.register(nome)
            CDProto.send_msg(sock,message)


        else:
            message = CDProto.message(str(line),canal)
            CDProto.send_msg(sock,message)




  

    
    
    
    








