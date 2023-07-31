import enum
import json
import pickle
import socket
import xml.etree.ElementTree as ET


class Serializer(enum.Enum):
    """Possible message serializers."""

    JSON = 0
    XML = 1
    PICKLE = 2


class Message:
    """Message Type."""
    def __init__(self,command):
        self.command = command
    def __repr__(self):
        return '{"command": '
    

class RegisterMessage(Message):
    def __init__(self, command,code):
        super().__init__(command)
        self.code = code

    def __repr__(self):
        return super().__repr__() + f'"{self.command}", "code": "{self.code}"' + '}'
    
    def PickleMsg(self):
        return {"command": self.command, "code": self.code}
    
    def XMLMsg(self):
        return f'<?xml version="1.0"?><data command="{self.command}" code="{self.code}"></data>'
    


    
class SubMessage(Message):
    def __init__(self, command,topic):
        super().__init__(command)
        self.topic = topic

    def __repr__(self):
        return super().__repr__() + f'"{self.command}", "topic": "{self.topic}"' + '}'
    
    
    def PickleMsg(self):
        return {"command": self.command, "topic": self.topic}
    
    def XMLMsg(self):
        return f'<?xml version="1.0"?><data command="{self.command}" topic="{self.topic}"></data>'
    
class PubMessage(Message):
    def __init__(self, command,topic, value):
        super().__init__(command)
        self.topic = topic
        self.value = value

    def __repr__(self):
        return super().__repr__() + f'"{self.command}", "topic": "{self.topic}", "value": {self.value}' + '}'
    
    def PickleMsg(self):
        return {"command": self.command, "topic": self.topic, "value": self.value}
    
    def XMLMsg(self):
        return f'<?xml version="1.0"?><data command="{self.command}" topic="{self.topic}" value="{self.value}"></data>'
    

class AskList(Message):
    def __init__(self, command):
        super().__init__(command)

    def __repr__(self):
        return super().__repr__() + f'"{self.command}"' + '}'

    def PickleMsg(self):
        return {"command": self.command}
    
    def XMLMsg(self):
        return f'<?xml version="1.0"?><data command="{self.command}"></data>'


    
class ListMsg(Message):
    def __init__(self, command, topics):
        super().__init__(command)
        self.topics = topics

    def __repr__(self):
        return super().__repr__() + f'"{self.command}", "topics": {self.topics}' + '}'
    
    def PickleMsg(self):
        return {"command": self.command, "topics": self.topics}
    
    def XMLMsg(self):
        return f'<?xml version="1.0"?><data command="{self.command}" topics="{self.topics}"></data>'
    


class CancelMsg(Message):
    def __init__(self, command,topic):
        super().__init__(command)
        self.topic = topic

    def __repr__(self):
        return super().__repr__() + f'"{self.command}", "topic": "{self.topic}"' + '}'
    
    def PickleMsg(self):
        return {"command": self.command, "topic": self.topic}
    
    def XMLMsg(self):
        return f'<?xml version="1.0"?><data command="{self.command}" topic="{self.topic}"></data>'

class Protocol:

    
    @classmethod
    def register(cls, code) -> RegisterMessage:
        return RegisterMessage('register', code)

    @classmethod
    def subscribe(cls, topic: str) -> SubMessage:
        return SubMessage('sub', topic)
    
    @classmethod
    def publish(cls, topic: str,value) -> PubMessage:
        return PubMessage('pub', topic, value)
    
    @classmethod
    def ask_list(cls) -> AskList:
        return AskList('ask')

    @classmethod
    def list(cls, topics) -> ListMsg:
        return ListMsg('list', topics)
    
    @classmethod
    def cancel(cls, topic: str) -> CancelMsg:
        return CancelMsg('cancel', topic)
    

    @classmethod
    def send_msg(cls, connection: socket, msg: Message, code):

        if code == None: code = 0

        if type(code) == str:
            code = int(code)    

        
        connection.send(code.to_bytes(1, 'big'))

        if code == Serializer.JSON or code == 0:
            message = json.loads(msg.__repr__())
            message = json.dumps(message).encode('utf-8')
            connection.send(len(message).to_bytes(2, 'big'))
            connection.send(message)

        elif code == Serializer.XML or code == 1:
            message = msg.XMLMsg().encode('utf-8')
            connection.send(len(message).to_bytes(2, 'big'))
            connection.send(message)

        elif code == Serializer.PICKLE or code == 2:
            message = pickle.dumps(msg.PickleMsg())
            connection.send(len(message).to_bytes(2, 'big'))
            connection.send(message)

    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        
        code = int.from_bytes(connection.recv(1), 'big')
        miniHeader = int.from_bytes(connection.recv(2), 'big')
        
        if miniHeader == 0:
            return None
        
        try:
            if code == 0:
                tempMsg = connection.recv(miniHeader).decode('utf-8')
                message = json.loads(tempMsg)

            elif code == 1:
                tempMsg = connection.recv(miniHeader).decode('utf-8')
                message = {}
                root = ET.fromstring(tempMsg)
                for node in root.keys():
                    message[node] = root.get(node)

            elif code == 2:
                tempMsg = connection.recv(miniHeader)
                message = pickle.loads(tempMsg)

        except json.JSONDecodeError as err:
            raise ProtocolBadFormat(tempMsg)

        command = message["command"]

        if command == "register":
            return cls.register(message["code"])

        elif command == "sub":
            return cls.subscribe(message["topic"])

        elif command == "pub":
            return cls.publish(message["topic"], message["value"])

        elif command == "ask":
            return cls.ask_list()
        
        elif command == "list":
            return cls.list(message["topics"])
        
        elif command == "cancel":
            return cls.cancel(message["topic"])

        else:
            return None
        
class ProtocolBadFormat(Exception):

    def __init__(self, original_msg: bytes=None):
        self._original = original_msg

