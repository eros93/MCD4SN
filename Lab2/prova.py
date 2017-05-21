
from collections import deque

from numpy import random
import simpy
import sys
import os

sessionTime = random.lognormal(8.492, 1.545)
#print sessionTime

f = open("throughput.txt","r")
data = f.readlines()
f.close()
intMaxLine = len(data)
indexLine = random.randint(1, intMaxLine)
line = data[indexLine]
# fileSize [Byte]
fileSize,throughput = line.split()
uploadTime = (int(fileSize)*8)/(float(throughput))
print fileSize
print throughput
print uploadTime
