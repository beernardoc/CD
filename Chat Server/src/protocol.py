"""Protocol for chat server - Computação Distribuida Assignment 1."""
import json
from datetime import datetime
from socket import socket


class Message:
    """Message Type."""
    def __init__(self,command):
        self.command = command
    def __str__(self):
        return '{"command": '
        

    
class JoinMessage(Message):
    """Message to join a chat channel."""
    def __init__(self, command,channel):
        super().__init__(command)
        self.channel = channel

    def __str__(self):
        return super().__str__() + f'"join", "channel": "{self.channel}"' + '}'


class RegisterMessage(Message):
    """Message to register username in the server."""
    def __init__(self, command,user):
        super().__init__(command)
        self.user = user

    def __str__(self):
        return super().__str__() + f'"register", "user": "{self.user}"' + '}'

    
class TextMessage(Message):
    """Message to chat with other clients."""
    def __init__(self, command,message,channel,ts):
        super().__init__(command)
        self.message = message
        self.channel = channel
        self.ts = ts

    def __str__(self):
        if self.channel is not None:
            return f'{{"command": "message", "message": "{self.message}", "channel": "{self.channel}", "ts": {self.ts}}}'
        else:
            return f'{{"command": "message", "message": "{self.message}", "ts": {self.ts}}}'

       

class CDProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def register(cls, username: str) -> RegisterMessage:
        """Creates a RegisterMessage object."""
        return RegisterMessage("register",username)

    @classmethod
    def join(cls, channel: str) -> JoinMessage:
        """Creates a JoinMessage object."""
        return JoinMessage("join", channel)

    @classmethod
    def message(cls, message: str, channel: str = None) -> TextMessage:
        """Creates a TextMessage object."""
        ts = int(datetime.now().timestamp())
        return TextMessage("message", message.rstrip(),channel,ts)

    @classmethod
    def send_msg(cls, connection: socket, msg: Message):
        """Sends through a connection a Message object."""
        
        if type(msg) is RegisterMessage:
            json_msg = json.dumps({"command": "register", "user": msg.user}).encode("utf-8")
        elif type(msg) is JoinMessage:
            json_msg = json.dumps({"command": "join", "channel": msg.channel}).encode("utf-8")
        elif type(msg) is TextMessage:
            if msg.channel == None:
                json_msg = json.dumps({"command": "message", "message": msg.message, "ts": int(datetime.now().timestamp())}).encode('utf-8')
            else:
                json_msg = json.dumps({"command": "message", "message": msg.message,  "channel": msg.channel, "ts": int(datetime.now().timestamp())}).encode('utf-8')
           

        head = len(json_msg).to_bytes(2, "big")
        connection.sendall(head + json_msg)
            

    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        """Receives through a connection a Message object."""
    
        dheader = connection.recv(2)

        if dheader:
            header = int.from_bytes(dheader, "big")
            data_msg = connection.recv(header).decode("utf-8")

            try:
                msg = json.loads(data_msg);
            except json.JSONDecodeError:
                raise CDProtoBadFormat(data_msg)
            
            
            if msg['command'] == "register":
                user = msg['user']
                return CDProto.register(user)
            elif msg['command'] == "join":
                channel = msg['channel']
                #print(channel)
                return CDProto.join(str(channel))
            elif msg['command'] == "message":
                        message = msg['message']
                        return CDProto.message(str(message), msg.get("channel"))
            
        else:
            return None

          

class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")
