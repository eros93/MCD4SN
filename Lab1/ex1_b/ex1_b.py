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

#SERVICE_TIME = [3.0] # it is the inverse of the service rate (speed)
ARRIVAL_TIME = [10.0]
SERVICE_TIME = numpy.linspace(1.0, 10.0, num=NUM)
#ARRIVAL_TIME = numpy.linspace(1.0, 10.0, num = NUM)

A = 1
B = 5
QCAPACITY = 100

CONF_LEVEL = 0.9
NUM_BEANS = 10

NUM_SERVER = 1
SIM_TIME = 1000000


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
            # print "A request was discarded"
            # print ("Request satisfied at ", self.env.now)

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
    def arrival_process(self, web_service):
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
                self.env.process(web_service.service_process)
                # print "process request number : %d " %(i+1)


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


    x = 0
    for servicerate in SERVICE_TIME:
        y = 0
        for arrivalrate in ARRIVAL_TIME:
            random.seed(RANDOM_SEED)

            env = simpy.Environment()

            # arrival
            request = RequestArrival(env, arrivalrate)

            # web service
            webserver = WebServer(env, NUM_SERVER, QCAPACITY, servicerate)

            # starts the arrival process
            env.process(request.arrival_process(webserver))

            # simulate until SIM_TIME
            env.run(until=SIM_TIME)

            # Statistics
            txt.write("Arrival rate [lambda]: %f - Service rate [u]: %f \n" % (arrivalrate, servicerate))
            txt.write("Number of requests: %d \t" % len(request.inter_arrival))
            txt.write("Number of requests satisfied: %d \n" % len(webserver.service_time))
            txt.write("Number of requests not satisfied: %d \n" % (len(request.inter_arrival) - len(webserver.service_time)))
            txt.write("Number of discarded requests: %d\n" %webserver.discarded)

            # truncate inter_arrival list when not all are satisfied
            del request.inter_arrival[(len(webserver.service_time)):]

            # Calculate Vector of response time
            response_time = [i[0] - i[1] for i in zip(webserver.service_time, request.inter_arrival)]
            mean_response_time[x,y] = numpy.mean(response_time)
            conf_int_tmp = t.interval(CONF_LEVEL, NUM_BEANS-1, mean_response_time[x,y], (numpy.std(response_time))/math.sqrt(NUM_BEANS))
            conf_int_rt[0,x] = conf_int_tmp[0]
            conf_int_rt[1,x] = conf_int_tmp[1]

            boccupancy_mean.append(numpy.mean(webserver.boccupancy))
            conf_int_tmp = t.interval(CONF_LEVEL, NUM_BEANS-1, boccupancy_mean[-1], (numpy.std(webserver.boccupancy))/math.sqrt(NUM_BEANS))
            conf_int_bo[0,x] = conf_int_tmp[0]
            conf_int_bo[1,x] = conf_int_tmp[1]

            ro.append(servicerate / arrivalrate)

            txt.write("Average RESPONSE TIME for requests: %f" % mean_response_time[x,y])
            txt.write("\n\n")

            # #plot Response Time
            # fig,(series, pdf, cdf) = pyplot.subplots(3, 1)
            #
            # series.plot(response_time)
            # series.set_xlabel("Sample")
            # series.set_ylabel("Response-Time")
            #
            # pdf.hist(response_time, bins=100, normed= True)
            # pdf.set_xlabel("Time")
            # pdf.set_ylabel("PDF")
            # #pdf.set_xbound(0, 15)
            #
            # cdf.hist(response_time, bins= 100, cumulative= True, normed= True)
            # cdf.set_xlabel("Time")
            # cdf.set_ylabel("P(Response Time <= x)")
            # cdf.set_ybound(0, 1)
            #
            # #plot buffer occupancy
            # fig2,(series, pdf, cdf) = pyplot.subplots(3, 1)
            #
            # series.plot(webserver.boccupancy)
            # series.set_xlabel("Sample")
            # series.set_ylabel("Buffer-Occupancy")
            #
            # pdf.hist(webserver.boccupancy, bins=100, normed= True)
            # pdf.set_xlabel("Time")
            # pdf.set_ylabel("PDF")
            # #pdf.set_xbound(0, 15)
            #
            # cdf.hist(webserver.boccupancy, bins= 100, cumulative= True, normed= True)
            # cdf.set_xlabel("Time")
            # cdf.set_ylabel("P(Buffer-Occupancy <= x)")
            # cdf.set_ybound(0, 1)
            #
            #pyplot.show()
            y += 1
        x += 1

    print("Simulation ended! Plotting some results...")

    #plot mean number of customers in queueing line
    fig1, responsetime_mean = pyplot.subplots(1,1)
    ci_rest = responsetime_mean.errorbar(ro, mean_response_time[:,0], xerr=0, yerr=conf_int_rt[:,:], fmt='.', color='c', label="Conf Int")
    emp_rest, = responsetime_mean.plot(ro,mean_response_time[:,0],label='Empirical')
    responsetime_mean.set_xlabel("ro")
    responsetime_mean.set_ylabel("mean response time ")
    responsetime_mean.grid()

    #plot mean number of customers in queueing line
    fig2, bo_mean = pyplot.subplots(1,1)
    ci_bo = bo_mean.errorbar(ro, boccupancy_mean, xerr=0, yerr=conf_int_bo[:,:], fmt='.', color='c', label="Conf Int")
    emp_bo, = bo_mean.plot(ro,boccupancy_mean, label='Empirical')
    bo_mean.set_xlabel("ro")
    bo_mean.set_ylabel("mean buffer occupancy")
    bo_mean.grid()

    responsetime_mean.legend(handles=[emp_rest,ci_rest])
    bo_mean.legend(handles=[emp_bo,ci_bo])



    pyplot.show()