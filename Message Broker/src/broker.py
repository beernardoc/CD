"""Message Broker"""
import enum
from typing import Dict, List, Any, Tuple
import socket
import selectors
from src.protocol import Protocol as PC


class Serializer(enum.Enum):
    """Possible message serializers."""

    JSON = 0
    XML = 1
    PICKLE = 2


class Broker:
    """Implementation of a PubSub Message Broker."""

    def __init__(self):
        """Initialize broker."""
        self.canceled = False
        self._host = "localhost"
        self._port = 5000

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.selector = selectors.DefaultSelector()

        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self._host, self._port))
        self.socket.listen()
        #self.socket.setblocking(False)
        self.selector.register(self.socket, selectors.EVENT_READ, self.accept)

        self.Serializer = {}                                     
        self.topic_Serializer = {}                                 
        self.msg_topics={}                                        
        self.topics_producer = []                                  
        

    def accept(self, sock, mask):
        """Accept new connection."""
        conn, addr = sock.accept()
        #conn.setblocking(False)
        self.selector.register(conn, selectors.EVENT_READ, self.read)

        message = PC.recv_msg(conn)
        code = message.code

        if type(code) == str: code = int(code)

        if message:
            if code == 0 or code == Serializer.JSON:
                self.Serializer[conn] = Serializer.JSON
            elif code == 1 or code == Serializer.XML:
                self.Serializer[conn] = Serializer.XML
            elif code == 2 or code == Serializer.PICKLE:
                self.Serializer[conn] = Serializer.PICKLE


    
    def read(self, conn, mask):
        """Read from connection."""
        try:
            message = PC.recv_msg(conn)

            if message:
                
                

                if message.command == 'sub':
                    self.subscribe(message.topic, conn, self.Serializer[conn])

                elif message.command == 'pub':

                    self.put_topic(message.topic, message.value)
                    
                #elif message.command == "register":
                #    self.register(message.code, conn)

                elif message.command == 'ask':

                    PC.send_msg(conn, PC.list(self.list_topics()), self.Serializer[conn])

                elif message.command == 'cancel':
                    self.unsubscribe(message.topic, conn)

        except ConnectionError:
            print("desconectado")
            for x in self.topic_Serializer:
                list = self.topic_Serializer[x]
                for y in list:
                    if y[0] == conn:
                        self.topic_Serializer[x].remove(y)
                        break
                
            
            self.selector.unregister(conn)
            conn.close()




    def list_topics(self) -> List[str]:
        """Returns a list of strings containing all topics containing values."""
        list = []
        for key in self.msg_topics:
            list.append(key)
        return list

    def get_topic(self, topic):
        """Returns the currently stored value in topic."""
        if topic in self.msg_topics:
            return self.msg_topics[topic]
        else:
            return None

    def put_topic(self, topic, value):
        """Store in topic the value."""
        self.msg_topics[topic] = value

        if topic not in self.topics_producer:
            self.topics_producer.append(topic)


        if topic not in self.topic_Serializer:
            self.topic_Serializer[topic] = []    
            for t in self.topic_Serializer:
                if t in topic:
                    for sub in self.list_subscriptions(t):
                        if sub not in self.list_subscriptions(topic):
                            self.topic_Serializer[topic].append(sub)
        
        if topic in self.topic_Serializer:
            for sub in self.list_subscriptions(topic):
                PC.send_msg(sub[0],PC.publish(topic,value), sub[1].value)

            

    def list_subscriptions(self, topic: str) -> List[Tuple[socket.socket, Serializer]]:
        """Provide list of subscribers to a given topic."""
        if topic in self.topic_Serializer:
            return self.topic_Serializer[topic]
        return []

    def subscribe(self, topic: str, address: socket.socket, _format: Serializer = None):
        """Subscribe to topic by client in address."""
        #check if topic exists
        if topic not in self.topic_Serializer:
            self.topic_Serializer[topic] = []    
            for t in self.topic_Serializer:
                if t in topic:
                    for sub in self.list_subscriptions(t):
                        if sub not in self.list_subscriptions(topic):
                            self.topic_Serializer[topic].append(sub)


        self.topic_Serializer[topic].append((address,_format))

        if topic in self.msg_topics:
            PC.send_msg(address,PC.publish(topic,self.msg_topics[topic]), _format.value)

           

    def unsubscribe(self, topic, address):
        """Unsubscribe to topic by client in address."""
        if topic in self.topic_Serializer:
            for sub in self.topic_Serializer[topic]:
                if sub[0] == address: self.topic_Serializer[topic].remove(sub)



    def acknowledge(self, conn, serialization_code):
        """Acknowledge new connection and its serialization type."""
        serialization_type = {
            0: Serializer.JSON,
            1: Serializer.XML,
            2: Serializer.PICKLE,
            Serializer.JSON: Serializer.JSON,
            Serializer.XML: Serializer.XML,
            Serializer.PICKLE: Serializer.PICKLE,
            None: Serializer.JSON
        }.get(serialization_code)

        if serialization_type:
            self.serial_types[conn] = serialization_type

    def create_topic(self, topic: str):
        """Create topic."""
        self.msg_topics.append(topic)
        self.topic_Serializer[topic] = []

        for i in self.msg_topics:
            if (topic.startswith(i)):
                for consumer in self.topic_Serializer[i]:
                    if consumer not in self.topic_Serializer[topic]:
                        self.topic_Serializer[topic].append(consumer)

    def run(self):
        """Run until canceled."""

        while not self.canceled:
            events = self.selector.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)
            pass
