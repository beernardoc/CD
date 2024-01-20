"""CD Chat server program."""
import json
import logging
import socket
import selectors
import sys

from .protocol import CDProto
logging.basicConfig(filename="server.log", level=logging.DEBUG)




class Server:
    """Chat Server process."""

    def __init__(self):
        global host
        global port
        global sock
        global selec
        global user
        selec = selectors.DefaultSelector()
        user = {None:[]}
        host = "localhost"
        port = 2000
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.bind((host,port))
        print("SERVER: " + str(host) + " " + str(port))
        sock.listen(100)
        selec.register(sock,selectors.EVENT_READ,accept)
        
    
    

    def loop(self):
        """Loop indefinetely."""
        global host
        global sock
        
        while True:
            events = selec.select()
            for key,mask in events:
                callback = key.data
                callback(key.fileobj,mask)
            


    
    
def accept(sock,mask):
    conn,addr = sock.accept()
    conn.setblocking(False)
    selec.register(conn,selectors.EVENT_READ,read)
    user[None].append(conn)


def read(conn,mask):
    global sock
    global selec
    dados = CDProto.recv_msg(conn)


    if dados:
      
        command = dados.command
        if(command == "register"):
            print(dados)


        elif(command == "join"):

            if(user.get(str(dados.channel))):
                user[str(dados.channel)].append(conn)

            else:
                user[str(dados.channel)] = []
                user[str(dados.channel)].append(conn)

            print(dados)

        elif(command == "message"):
                msg = CDProto.message(dados.message,dados.channel)
                print("mess")
                print(msg)
                for value in user[dados.channel]:
                    CDProto.send_msg(value,msg)
                

    else:
        for c in user.keys():
            if conn in user[c]:
                user[c].remove(conn)
        print(user)
        selec.unregister(conn)
        conn.close()
    


        

        
         




    



    
            
            
            


        

               



    

   





    
                