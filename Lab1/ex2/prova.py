import simpy
import random
import numpy
from matplotlib import pyplot
from scipy.stats import t
import math

reqs = []  # list of Request objects


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
# REQUEST Class
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

class Request(object):
    r_index = 0  # request ID (increasing)

    def __init__(self):
        self.id = Request.r_index
        Request.r_index += 1
        self.arrtime = 0
        self.sertime = 0

    def setArrivaTime(self, arrivalTime):
        self.arrtime = arrivalTime

    def setServiceTime(self, serviceTime):
        self.sertime = serviceTime



for i in range(10):
    req = Request()
    reqs.append(req)
    req.setArrivaTime(i+100)
    print reqs[-1].arrtime
