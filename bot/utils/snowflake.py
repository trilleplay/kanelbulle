import math, time
from random import randint

TOTAL_BITS = 64
EPOCH_BITS = 42
NODE_ID_BITS = 10
SEQUENCE_BITS = 12

maxNodeId = (int)(math.pow(2, NODE_ID_BITS) - 1)
maxSequence = (int)(math.pow(2, SEQUENCE_BITS) - 1)

CUSTOM_EPOCH = 1420070400000

nodeId = 0

lastTimestamp = -1
sequence = 0

def SequenceGenerator(_nodeId: int = None):
    global nodeId
    if _nodeId is None:
        nodeId = createNodeId()
        return
    if _nodeId < 0 or _nodeId > maxNodeId:
        raise ValueError('NodeId must be between {} and {}'.format(0, maxNodeId))
    nodeId = _nodeId

#long
def nextId():
    global lastTimestamp
    currentTimestamp = timestamp()

    if currentTimestamp < lastTimestamp:
        raise ValueError('Invalid System Clock!')

    if currentTimestamp == lastTimestamp:
        sequence = (sequence + 1) & maxSequence
        if sequence == 0:
            #Sequence Exhausted, wait till next millisecond.
            currentTimestamp = waitNextMillis(currentTimestamp)
    else:
        #reset sequence to start with zero for the next millisecond
        sequence = 0

    lastTimestamp = currentTimestamp

    id = currentTimestamp << (TOTAL_BITS - EPOCH_BITS)
    id |= (nodeId << (TOTAL_BITS - EPOCH_BITS - NODE_ID_BITS))
    id |= sequence
    return id

#Get current timestamp in milliseconds, adjust for the custom epoch.
def timestamp():
    return int(round(time.time() * 1000)) - CUSTOM_EPOCH

#Block and wait till next millisecond
def waitNextMillis(currentTimestamp):
    while currentTimestamp == lastTimestamp:
        currentTimestamp = timestamp()
    return currentTimestamp

def createNodeId():
    global maxNodeId
    nodeId = randint(100, 999) & maxNodeId
    return nodeId

print("[SNOWFLAKES] Snowflake module loaded! :catblush:")