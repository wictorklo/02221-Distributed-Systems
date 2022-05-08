from abc import abstractclassmethod
from typing import Optional
Protocol = {}

#We're not assuming IP right? 
class Message:
    data = {}
    def __init__(self, sender, receiver) -> None: 
        self.data = {
            "IP": {
                "SRC": sender,
                "DST": receiver
            }
        }
    
    @abstractclassmethod
    def handler(msg : 'Message', self : 'Node' = None) -> 'Message':
        pass

    def __str__(self):
        return str(self.data)
        

class TCP(Message):
    SYN, SYNACK, ACK = 1, 2, 3

    def __init__(self, sender, receiver, data) -> None:
        Message.__init__(self, sender, receiver)
        self.data["DATA"] = data
    
    def handler(msg : 'TCP', self : 'Node'):
        response = None
        match msg.data["DATA"]["FLAG"]:
            case  TCP.SYN:
                response = {
                    "FLAG": TCP.SYNACK
                }
            case TCP.SYNACK:
                response = {
                    "FLAG": TCP.ACK
                }
            case TCP.ACK:
                pass
            case _:
                return None
        if (response):
            return TCP(msg.data["IP"]["SRC"], msg.data["IP"]["DST"], response)
        else:
            return None

"""
New Protocol
class NewProtocol(Message):
    Define enumerations or constants, eg.
    SYN, ACK, SYNACK = 1, 2, 3

    Optional:
    def __init__(self, ...):
        Set initial data fields as needed.
        Call Parent-class as Message.__init__(sender : Node, receiver : Node)
        Parent data has mockup of IP by default.
    
    Important:
    Implement the method for handling the protocol
    For example the TCP mockup example will send different responses depending on the FLAG-parameter
    The node will call this method upon receiving the message. Returning a Message-object will cause the node to send a response
    Change the state of the calling Node by referencing 'self'
    def handler(msg : 'Message', self : 'Node') -> Message:
        response = None
        match msg.data[FIELD]:
            case a:
                ...
            case b:
                ...
            case _:
                ...
        return response
"""



class Node:
    name = ""

    def __init__(self, name : str):
        self.name = name
    
    def send(self, receiver : 'Node', msg: Message):
        receiver.recv(msg)

    def recv(self, msg : Message):
        sender = msg.data["IP"]["SRC"]
        handler = type(msg).handler
        response : Message = handler(msg, self)
        print(self.name, "received TCP message from", sender.name, "containing", msg.data)
        if response:
            self.send(sender, response)

Protocol = {
    "TCPSyn": {
        "Fields" : {"FLAG": TCP.SYN},
        "Next" : Protocol["TCPSynack"]
    },
    "TCPSynack": {
        "Fields" : {"FLAG": TCP.SYNACK},
        "Next" : Protocol["TCPAck"]
    },
    "TCPAck": {
        "Fields" : {"FLAG": TCP.ACK},
        "Next" : None
    }
}

alice = Node("Alice")
bob = Node("Bob")

alice.send(bob, TCP(alice, bob, {"FLAG": TCP.SYN}))