from single_step import SingleStepNI
from messages import *
from collections import deque
import util
import math

class DynamicRoutingNI:
    def __init__(self,
            ID : 'str', singleStepNI : 'SingleStepNI', routingTable, infoTable,
            defaultTimeoutOrigin = 100, defaultTimeoutRouting = 20,
            defaultRetriesOrigin = 5, defaultRetriesRouting = 3,
            defaultPingTimeout = 6, defaultInfoTimeout = 150):
        self.ID = ID
        self.singleStepNI = singleStepNI
        self.timeouts = {}
        self.timeoutHandlers = {}
        self.retries = {}
        self.timeoutStarts = {}
        self.payloadLog = set()
        self.predicastLog = set()
        self.incoming = deque()
        self.routingTable = routingTable
        self.infoTable = infoTable
        self.defaultTimeoutOrigin = defaultTimeoutOrigin
        self.defaultTimeoutRouting = defaultTimeoutRouting
        self.defaultRetriesOrigin = defaultRetriesOrigin
        self.defaultRetriesRouting = defaultRetriesRouting
        self.defaultPingTimeout = defaultPingTimeout
        self.defaultInfoTimeout = defaultInfoTimeout
        self.seq = 1
        self.clock = 0
        self.lastCorrections = {self.ID : self.clock}
        for ID in self.routingTable:
            if ID != self.ID:
                self.lastCorrections[ID] = 0
        self.timeouts["infocast"] = self.defaultInfoTimeout
        self.timeoutHandlers["infocast"] = self.__infocast

    def tick(self):
        for seq in list(self.timeouts.keys()):
            self.timeouts[seq] -= 1
            if self.timeouts[seq] <= 0:
                self.timeoutHandlers[seq]()
        if not self.routingTable[self.ID] == self.singleStepNI.neighbours:
            self.__correctRouting()


    #just used in first step
    def sendPayloadMessage(self,message : 'PayloadDRMessage'):
        message.autoComplete(self.ID,self.seq,self.clock)
        message.data["timestamp"] = self.clock
        seq = message.data['seq']
        if seq == self.seq:
            self.seq += 1

        if not seq in self.timeouts:
            self.timeouts[seq] = self.defaultTimeoutOrigin
            self.timeoutHandlers[seq] = (lambda : self.sendPayloadMessage(message))
            self.timeoutStarts[seq] = self.clock
        if not seq in self.retries:
            self.retries[seq] = self.defaultRetriesOrigin
        if self.retries[seq] <= 0:
            del self.timeouts[seq]
            del self.timeoutStarts[seq]
            del self.timeoutHandlers[seq]
            del self.retries[seq]
            return

        self.__sendMessage(message)

    def receiveMessage(self, message : 'DRMessage'):
        self.clock += 1
        #we treat no destination as broadcasts
        if 'destination' in message.data and message.data['destination'] != self.ID:
            self.__bounceMessage(message)
        elif message.data['type'] == 'payload':
            self.__receivePayloadMessage(message)
        elif message.data['type'] == 'payloadAck':
            self.__receivePayloadAckMessage(message)
        elif message.data['type'] == "ack":
            self.__receiveAckMessage(message)
            return #acks don't expect acks
        elif message.data['type'] == 'correction':
            self.__receiveCorrection(message)
            return #correction messages don't expect acks
        elif message.data['type'] == 'performCorrection':
            self.__correctRouting()
            return #performCorrection messages don't expect acks
        elif message.data['type'] == 'predicast':
            self.__receivePredicast(message)
            return #predicast messages don't expect acks
        elif message.data['type'] == 'info':
            self.__receiveInfo(message)
            return #info messages don't expect acks
        
        #we misuse the source field to store the source of the message we are acking
        #this scheme could lead to problems if we are excpecting acks from multiple nodes for the same message
        destination = self.__prevStep(message)
        if not destination:
            raise Exception("no previous node")
        ack = AckDRMessage()
        ack.data["seq"] = message.data["seq"]
        ack.data["source"] = message.data["source"]
        ack.data["destination"] = destination
        ack.data["ackedType"] = message.data["type"]
        ack.autoComplete(self.ID,self.seq,self.clock)
        
        ssMessage = PayloadSSMessage()
        ssMessage.data["payload"] = ack.getTransmit()
        ssMessage.data["destination"] = destination
        self.singleStepNI.sendPayloadMessage(ssMessage)
    
    def predicast(self,message : 'PredicastDRMessage'):
        self.predicastLog.add((message.data["source"],message.data["seq"]))
        self.__sendPredicast(message)

    def newPosition(self,xpos,ypos):
        self.clock += 1
        self.infoTable[self.ID]["xpos"] = xpos
        self.infoTable[self.ID]["ypos"] = ypos
        self.infoTable[self.ID]["timestamp"] = self.clock
    
    def __sendPredicast(self,message : 'PredicastDRMessage'):
        message.autoComplete(self.ID,self.seq,self.clock)
        if message.data["source"] == self.ID and message.data["seq"] == self.seq:
            self.seq += 1

        destinations : 'set[str]' = self.fulfillsPredicate(message.data["predicate"])
        if self.ID in destinations:
            destinations.remove(self.ID)
        if message.data["source"] in destinations:
            destinations.remove(message.data["source"])
        self.__multicast(message,destinations)

    def __receivePredicast(self, message : 'PredicastDRMessage'):
        if (message.data["source"],message.data["seq"]) in self.predicastLog:
            return #already handled
        self.predicastLog.add((message.data["source"],message.data["seq"]))
        if self.__evaluatePredicate(message.data["predicate"],self.ID):
            self.incoming.append(message.data["payload"])
        self.__sendPredicast(message)

    def __multicast(self, message : 'Message',destinations):
        for destination in destinations:
            route = util.route(self.ID,destination,self.routingTable)
            if not route:
                return "NoRoute"
            ssMessage = PayloadSSMessage()
            ssMessage.data["payload"] = message.getTransmit()
            ssMessage.data["destination"] = route[1]
            self.singleStepNI.sendPayloadMessage(ssMessage)

    def __receiveInfo(self, message : 'InfoDRMessage'):
        if message.data["info"]["timestamp"] > self.infoTable[message.data["source"]]["timestamp"]:
            self.infoTable[message.data["source"]] = message.data["info"]

    def __infocast(self):
        self.clock += 1
        self.timeouts["infocast"] = self.defaultInfoTimeout
        self.infoTable[self.ID]["timestamp"] = self.clock
        message = InfoDRMessage()
        message.data["info"] = self.infoTable[self.ID]
        message.autoComplete(self.ID,self.seq,self.clock)
        self.seq += 1

        bcMessage = BroadcastMessage()
        bcMessage.data["payload"] = message.getTransmit()
        self.singleStepNI.broadcast(bcMessage)

    #used in intermediate steps
    #we assume message contains necessary info
    def __sendMessage(self,message : 'PayloadDRMessage'):
        self.clock += 1
        #autocomplete
        message.autoComplete(self.ID,self.seq,self.clock)
        if message.data["source"] == self.ID and message.data["seq"] == self.seq:
            self.seq += 1

        seq = (message.data["source"],message.data["seq"],message.data["type"])

        #handle timeouts
        if seq in self.timeouts and self.timeoutStarts[seq] > self.lastCorrections[self.ID]:
            self.__correctRouting()
            self.timeouts[seq] = self.defaultTimeoutRouting
            return "Correcting"
        if not seq in self.timeouts:
            self.timeoutStarts[seq] = self.clock
            self.timeouts[seq] = self.defaultTimeoutRouting
            self.timeoutHandlers[seq] = (lambda : self.__sendMessage(message))
        
        #handle retries
        if not seq in self.retries:
            self.retries[seq] = self.defaultRetriesRouting
        if self.retries[seq] <= 0:
            del self.timeouts[seq]
            del self.timeoutHandlers[seq]
            del self.retries[seq]
            del self.timeoutStarts[seq]
            return "RetriesExhausted"
        self.retries[seq] -= 1

        #add route if missing or outdated
        if not "route" in message.data or self.timeoutStarts[seq] < self.lastCorrections[self.ID]:
            if not self.__findRoute(message):
                return "NoRoute"

        #send through SS layer
        nextStepID = message.data["route"][self.ID]
        ssMessage = PayloadSSMessage()
        ssMessage.data["payload"] = message.getTransmit()
        ssMessage.data["destination"] = nextStepID
        self.singleStepNI.sendPayloadMessage(ssMessage)
        return "Success"

    def __bounceMessage(self, message : 'DRMessage'):
        #if bounce is not possible
        if not message.data["route"][self.ID] in self.routingTable[self.ID]:
            #send correction back to source
            correction = CorrectionDRMessage()
            correction.data["neighbours"] = list(self.routingTable[self.ID])
            correction.data["destination"] = message.data["source"]
            self.__sendMessage(correction)

            #find actual path
            if not self.__findRoute(message):
                return "NoRoute"
        return self.__sendMessage(message)

    def __receivePayloadMessage(self, message : 'PayloadDRMessage'):
        seq = message.data['seq']
        source = message.data['source']
        ack = PayloadAckDRMessage()
        #we missuse source field for original source to avoid duplicate seqs
        ack.data['source'] = source
        ack.data['destination'] = source
        ack.data['seq'] = seq
        self.__sendMessage(ack)
        if (seq,source) in self.payloadLog: 
            return #already received
        self.payloadLog.add((seq,source))
        self.incoming.append(message.data['payload'])

    def __receivePayloadAckMessage(self, message : 'PayloadAckDRMessage'):
        seq = message.data['seq']
        if seq in self.timeouts:
            del self.timeouts[seq]
            del self.timeoutHandlers[seq]
            del self.retries[seq]
            del self.timeoutStarts[seq]
    
    def __receiveAckMessage(self, message : 'AckDRMessage'):
        seq = (message.data['source'],message.data['seq'],message.data['ackedType'])
        if seq in self.timeouts:
            del self.timeouts[seq]
            del self.timeoutHandlers[seq]
            del self.retries[seq]
            del self.timeoutStarts[seq]

    def __receiveCorrection(self, message : 'CorrectionDRMessage'):
        if not message.data["timestamp"] > self.lastCorrections[message.data["source"]]:
            return #ignore floating corpse
        self.lastCorrections[message.data["source"]] = message.data["timestamp"]
        self.routingTable[message.data["source"]] = set(message.data["neighbours"])

    def __correctRouting(self):
        self.clock += 1
        if not "correction" in self.timeouts:
            self.singleStepNI.ping()
            self.timeouts["correction"] = self.defaultPingTimeout
            self.timeoutHandlers["correction"] = self.__correctionTimeout

    def __correctionTimeout(self):
        self.clock += 1
        del self.timeouts["correction"]
        del self.timeoutHandlers["correction"]
        self.lastCorrections[self.ID] = self.clock

        if self.routingTable[self.ID] != self.singleStepNI.neighbours:
            #correct neighbours
            self.routingTable[self.ID] = self.singleStepNI.neighbours

            #broadcast new neighbours
            correction = CorrectionDRMessage()
            correction.data["neighbours"] = list(self.routingTable[self.ID])
            correction.data["timestamp"] = self.clock 
            correction.autoComplete(self.ID,self.seq,self.clock)

            self.clock += 1
            self.seq += 1
            bcMessage = BroadcastMessage()
            bcMessage.data["payload"] = correction.getTransmit()

            self.singleStepNI.broadcast(bcMessage)

            #tell neighbours to correct
            for ID in self.routingTable[self.ID]:
                performCorrection = PerformCorrectionDRMessage()
                performCorrection.data["destination"] = ID
                performCorrection.autoComplete(self.ID,self.seq,self.clock)
                self.seq += 1
                self.clock += 1
                ssMessage = PayloadSSMessage()
                ssMessage.data["payload"] = performCorrection.getTransmit()
                ssMessage.data["destination"] = ID
                self.singleStepNI.sendPayloadMessage(ssMessage)

    def __findRoute(self, message : 'DRMessage'):
        route = util.route(self.ID, message.data["destination"], self.routingTable)
        routeMap = {}
        for i in range(1,len(route)):
            routeMap[route[i-1]] = route[i]
        message.data["route"] = routeMap
        return route

    def __prevStep(self, message : 'DRMessage'):
        route = message.data["route"]
        for prev in route:
            nxt = route[prev]
            if nxt == self.ID:
                return prev
        return None

    def fulfillsPredicate(self, predicate):
        fulfills = set([])
        for DroneID in self.infoTable:
            if self.__evaluatePredicate(predicate,DroneID):
                fulfills.add(DroneID)
        return fulfills

#Predicate language
#pred =
#   | true
#   | false
#   | not (pred)
#   | and (pred, pred)
#   | or (pred,pred)
#   | eq (exp,exp)
#   | leq (exp,exp)
#   | less (exp,exp)
#   | typeA (droneID)
#   | typeB (droneID)
#
#exp =
#   | xpos (droneID)
#   | ypos (droneID)
#   | num (num)
#   | dist (exp,exp,exp,exp)
#   | plus (exp,exp)
#   | minus (exp,exp)
#   | times (exp,exp)
#   | div (exp,exp)
#   | sqrt (exp)
#
#droneID =
#   | varDrone
#   | drone (str)

    #evaluate predicate with some failsafes
    def __evaluatePredicate(self, predicate, DroneID):
        try:
            eval = self.__evaluatePredicateRec(predicate,DroneID)
        except ValueError:
            return False
        except ZeroDivisionError:
            return False
        if not eval:
            return False
        return eval

    def __evaluatePredicateRec(self, predicate, DroneID):
        if predicate[0] == "true":
            return True
        if predicate[0] == "false":
            return False
        if predicate[0] == "not":
            return not self.__evaluatePredicateRec(predicate[1],DroneID)
        if predicate[0] == "and":
            if not self.__evaluatePredicateRec(predicate[1],DroneID):
                return False
            if not self.__evaluatePredicateRec(predicate[2],DroneID):
                return False
            return True
        if predicate[0] == "or":
            if self.__evaluatePredicateRec(predicate[1],DroneID):
                return True
            if self.__evaluatePredicateRec(predicate[2],DroneID):
                return True
            return False
        if predicate[0] == "eq":
            x = self.__evaluateExpression(predicate[1],DroneID)
            y = self.__evaluateExpression(predicate[2],DroneID)
            return x == y
        if predicate[0] == "less":
            x = self.__evaluateExpression(predicate[1],DroneID)
            y = self.__evaluateExpression(predicate[2],DroneID)
            return x < y
        if predicate[0] == "leq":
            x = self.__evaluateExpression(predicate[1],DroneID)
            y = self.__evaluateExpression(predicate[2],DroneID)
            return x <= y
        if predicate[0] == "typeA":
            droneID = self.__evaluateDroneID(predicate[1],DroneID)
            return self.infoTable[droneID]["type"] == "A"
        if predicate[0] == "typeB":
            droneID = self.__evaluateDroneID(predicate[1],DroneID)
            return self.infoTable[droneID]["type"] == "B"

    def __evaluateExpression(self, expression, DroneID):
        if expression[0] == "xpos":
            droneID = self.__evaluateDroneID(expression[1],DroneID)
            return self.infoTable[droneID]["xpos"]
        if expression[0] == "ypos":
            droneID = self.__evaluateDroneID(expression[1],DroneID)
            return self.infoTable[droneID]["ypos"]
        if expression[0] == "num":
            return expression[1]
        if expression[0] == "plus":
            x = self.__evaluateExpression(expression[1],DroneID)
            y = self.__evaluateExpression(expression[2],DroneID)
            return x + y
        if expression[0] == "minus":
            x = self.__evaluateExpression(expression[1],DroneID)
            y = self.__evaluateExpression(expression[2],DroneID)
            return x - y
        if expression[0] == "times":
            x = self.__evaluateExpression(expression[1],DroneID)
            y = self.__evaluateExpression(expression[2],DroneID)
            return x * y
        if expression[0] == "div":
            x = self.__evaluateExpression(expression[1],DroneID)
            y = self.__evaluateExpression(expression[2],DroneID)
            return x / y
        if expression[0] == "sqrt":
            x = self.__evaluateExpression(expression[1],DroneID)
            return math.sqrt(x)
        if expression[0] == "dist":
            x1 = self.__evaluateExpression(expression[1],DroneID)
            y1 = self.__evaluateExpression(expression[2],DroneID)
            x2 = self.__evaluateExpression(expression[3],DroneID)
            y2 = self.__evaluateExpression(expression[4],DroneID)
            x = x2 - x1
            y = y2 - y1
            return math.sqrt(x * x + y * y)
        

    def __evaluateDroneID(self, idExpression, DroneID):
        if idExpression[0] == "varDrone":
            return DroneID
        if idExpression[0] == "drone":
            return idExpression[1]
        

#TODO: 
#tests