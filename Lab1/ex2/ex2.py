import simpy
import random
import numpy
from matplotlib import pyplot
from scipy.stats import t
import math

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
# CONSTANTS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
RANDOM_SEED = 7

# SERVICE_RATE = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
# ARRIVAL_RATE = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
NUM = 20

SERVICE_TIME1 = 3.0 #[Front-End] it is the inverse of the service rate (speed)
SERVICE_TIME2 = 6.0 #[Back-End]

ARRIVAL_TIME = 10.0
#SERVICE_TIME = numpy.linspace(1.0, 10.0, num=NUM)
#ARRIVAL_TIME = numpy.linspace(1.0, 10.0, num = NUM)

#Batch dimension
A = 1
B = 5

#buffers dimension
B1 = 100
B2 = 50

#probability of reqs not satisfied by Front End
P = 0.2

CONF_LEVEL = 0.9
NUM_BEANS = 10

NUM_SERVER = 1
SIM_TIME = 10000


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
# WEB SERVER Class
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
class WebServer(object):
    def __init__(self, environ, numserver, qcapacity, service_rate):
        # define the number of servers in parallel
        self.servers = simpy.Resource(environ, numserver)

        # holds samples of request-processing time
        self.service_time = []
        self.service_rate = service_rate

        self.env = environ

        self.instant_boccupancy = 0
        self.boccupancy = []

        self.instant_qsize = 0
        self.qsize = []

        self.qcapacity = qcapacity
        self.discarded = 0

    @property
    def service_process(self):
        self.instant_qsize += 1

        if (self.instant_boccupancy <= self.qcapacity ):
            # make a server request
            with self.servers.request() as request:
                self.instant_boccupancy += 1
                # print ("Request has required the resource at ", self.env.now)
                yield request
                self.instant_boccupancy -= 1
                # print ("Request has received the resource at ", self.env.now)

                # once the servers is free, wait until service is finished
                service_time = random.expovariate(lambd=1.0 / self.service_rate)
                self.boccupancy.append(self.instant_boccupancy)
                # yield an event to the simulator
                yield self.env.timeout(service_time)
                self.service_time.append(self.env.now)
                self.instant_qsize -= 1
                self.qsize.append(self.instant_qsize)
        else:
            self.discarded += 1
            print "A request was discarded"
            #  print ("Request satisfied at ", self.env.now)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
# REQUEST Class
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

class RequestArrival(object):
    # constructor
    def __init__(self, environ, arrival_rate):
        # holds samples of inter-arrival time
        self.inter_arrival = []

        self.arrival_rate = arrival_rate
        self.env = environ

    # execute the process
    def arrival_process(self, web_service1, web_service2):
        while True:
            # sample the time to next arrival
            inter_arrival = random.expovariate(lambd=1.0 / self.arrival_rate)
            batches_dim = numpy.random.random_integers(A,B)

            # yield an event to the simulator
            yield self.env.timeout(inter_arrival)

            # a request has arrived - request the service to the server
            # print ("batch of dimension %d Request has arrived at %r" %(batches_dim, self.env.now))
            for i in range(batches_dim):
                self.inter_arrival.append(self.env.now)  # sample time of arrival
                self.env.process(web_service1.service_process)
                #print "Front_End request number : %d is finished " %(i+1)

                coin = numpy.random.random()
                if (coin < P):
                    #print coin
                    self.env.process(web_service2.service_process)
                    #web_service1.service_time[-1] = web_service2.service_time[-1] #insert the correct service time for that req
                    #print "Back_End request number : %d is finished " % (i+1)




# ----------------------------------------------------------------------------------------------#
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
# MAIN
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


if __name__ == '__main__':

    print("Starting the simulation... ")

    txt = open("result_simulation.txt", "w+")
    txt.truncate()

    mean_response_time = numpy.zeros((NUM,NUM))
    conf_int_rt = numpy.zeros((2,NUM))

    boccupancy_mean = []
    conf_int_bo = numpy.zeros((2,NUM))

    ro = []



    random.seed(RANDOM_SEED)

    env = simpy.Environment()

    # arrival
    arrival = RequestArrival(env, ARRIVAL_TIME)


    # web service
    frontEnd = WebServer(env, NUM_SERVER, B1, SERVICE_TIME1)
    backEnd = WebServer(env, NUM_SERVER, B2, SERVICE_TIME2)


    # starts the arrival process
    env.process(arrival.arrival_process(frontEnd,backEnd))

    # simulate until SIM_TIME
    env.run(until=SIM_TIME)

    # truncate inter_arrival list when not all are satisfied
    del arrival.inter_arrival[(len(frontEnd.service_time)):]

    # Calculate Vector of response time
    response_time = [i[0] - i[1] for i in zip(frontEnd.service_time, arrival.inter_arrival)]


    #plot Response Time
    fig,(series, pdf, cdf) = pyplot.subplots(3, 1)

    series.plot(response_time)
    series.set_xlabel("Sample")
    series.set_ylabel("Overall Response-Time")

    pdf.hist(response_time, bins=100, normed= True)
    pdf.set_xlabel("Time")
    pdf.set_ylabel("PDF")
    #pdf.set_xbound(0, 15)

    cdf.hist(response_time, bins= 100, cumulative= True, normed= True)
    cdf.set_xlabel("Time")
    cdf.set_ylabel("P(Response Time <= x)")
    cdf.set_ybound(0, 1)

    #plot buffer occupancy FrontEnd
    fig2,(series, pdf, cdf) = pyplot.subplots(3, 1)

    series.plot(frontEnd.boccupancy)
    series.set_xlabel("Sample")
    series.set_ylabel("FrontEnd Buffer-Occupancy")

    pdf.hist(frontEnd.boccupancy, bins=100, normed= True)
    pdf.set_xlabel("Time")
    pdf.set_ylabel("PDF")
    #pdf.set_xbound(0, 15)

    cdf.hist(frontEnd.boccupancy, bins= 100, cumulative= True, normed= True)
    cdf.set_xlabel("Time")
    cdf.set_ylabel("P(Buffer-Occupancy <= x)")
    cdf.set_ybound(0, 1)

    #plot buffer occupancy BackEnd
    fig3,(series, pdf, cdf) = pyplot.subplots(3, 1)

    series.plot(backEnd.boccupancy)
    series.set_xlabel("Sample")
    series.set_ylabel("BackEnd Buffer-Occupancy")

    pdf.hist(backEnd.boccupancy, bins=100, normed= True)
    pdf.set_xlabel("Time")
    pdf.set_ylabel("PDF")
    #pdf.set_xbound(0, 15)

    cdf.hist(backEnd.boccupancy, bins= 100, cumulative= True, normed= True)
    cdf.set_xlabel("Time")
    cdf.set_ylabel("P(Buffer-Occupancy <= x)")
    cdf.set_ybound(0, 1)

    pyplot.show()

