"""Middleware to communicate with PubSub Message Broker."""
from collections.abc import Callable
from enum import Enum
import json
import pickle
from queue import LifoQueue, Empty
import selectors
from typing import Any
import socket
from src.protocol import Protocol as PC
import xml.etree.ElementTree as XMLTree


class MiddlewareType(Enum):
    """Middleware Type."""

    CONSUMER = 1
    PRODUCER = 2


class Queue:
    """Representation of Queue interface for both Consumers and Producers."""

    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        """Create Queue."""
        self.topic = topic
        self.type = _type
        self.serial = 0
        self.adress = ("localhost", 5000)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.selector = selectors.DefaultSelector()
        self.sock.connect(self.adress)
        self.selector.register(self.sock,selectors.EVENT_READ, self.pull)
        


    def push(self, value):
        """Sends data to broker."""
        message = PC.publish(self.topic,value)
        PC.send_msg(self.sock,message,self.serial)

    def pull(self) -> (str, Any):
        """Receives (topic, data) from broker.

        Should BLOCK the consumer!"""
        msg = PC.recv_msg(self.sock)
        if msg is None:
            return None
        return (msg.topic,msg.value)

        

    def list_topics(self, callback: Callable):
        """Lists all topics available in the broker."""
        message = PC.ask_list()
        PC.send_msg(self.sock,message,self.serial)

    def cancel(self):
        """Cancel subscription."""
        message = PC.cancel(self.topic)
        PC.send_msg(self.sock,message,self.serial)


class JSONQueue(Queue):
    """Queue implementation with JSON based serialization."""

    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        super().__init__(topic, _type)

        self.serial = 0
        PC.send_msg(self.sock,PC.register(self.serial),0)

        if _type == MiddlewareType.CONSUMER:
            PC.send_msg(self.sock,PC.subscribe(topic),self.serial)




class XMLQueue(Queue):
    """Queue implementation with XML based serialization."""
    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        super().__init__(topic, _type)

        self.serial = 1
        PC.send_msg(self.sock,PC.register(self.serial),0)

        if _type == MiddlewareType.CONSUMER:
            PC.send_msg(self.sock,PC.subscribe(topic),self.serial)
    


class PickleQueue(Queue):
    """Queue implementation with Pickle based serialization."""
    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        super().__init__(topic, _type)

        self.serial = 2
        PC.send_msg(self.sock,PC.register(self.serial),0)

        if _type == MiddlewareType.CONSUMER:
            PC.send_msg(self.sock,PC.subscribe(topic),self.serial)