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
NUM = 25

#SERVICE_TIME = [3.0] # it is the inverse of the service rate (speed)
ARRIVAL_TIME = [10.0]
SERVICE_TIME = numpy.linspace(1.0, 10.0, num=NUM)
#ARRIVAL_TIME = numpy.linspace(1.0, 10.0, num = NUM)

A = 1
B = 5
QCAPACITY = 50000

CONF_LEVEL = 0.9
DIM_BATCHES = 50000

NUM_SERVER = 1
SIM_TIME = 1500000


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

    random.seed(RANDOM_SEED)

    print("\nRunning the simulation... ")

    mean_response_time = numpy.zeros((NUM,NUM))
    conf_int_rt = numpy.zeros((2,NUM))

    boccupancy_mean = []
    conf_int_bo = numpy.zeros((2,NUM))

    ro = []


    x = 0
    for servicerate in SERVICE_TIME:
        y = 0
        for arrivalrate in ARRIVAL_TIME:

            env = simpy.Environment()

            # arrival
            request = RequestArrival(env, arrivalrate)

            # web service
            webserver = WebServer(env, NUM_SERVER, QCAPACITY, servicerate)

            # starts the arrival process
            env.process(request.arrival_process(webserver))


            # Batches analysis

            #Reset the data structures
            pointer_rt = 0
            pointer_bo = 0
            mean_response_time_batches = []
            boccupancy_mean_batches = []

            for index in range(1,(SIM_TIME/DIM_BATCHES)+1):
                # simulate until index*DIM_BATCHES
                env.run(until = index*DIM_BATCHES)

                # Statistics

                # take only the datas related to the one processed in the batch
                inter_arrival_batch = request.inter_arrival[ pointer_rt : len(webserver.service_time) ]
                service_time_batch = webserver.service_time[ pointer_rt : ]
                
                boccupancy_batch = webserver.boccupancy[ pointer_bo : ]

                # update pointer index
                pointer_rt = len(webserver.service_time)
                pointer_bo = len(webserver.boccupancy)

                # Calculate Vector of Response Times for the batch
                response_time = [ i[0] - i[1] for i in zip(service_time_batch, inter_arrival_batch) ]
                
                # Mean values estimation
                # Response Time
                batch_mean = numpy.mean(response_time)
                mean_response_time_batches.append(batch_mean)
                
                # Buffer Occupancy
                batch_mean = numpy.mean(boccupancy_batch)
                boccupancy_mean_batches.append(batch_mean)

            # print "\nmean_response_time_batches"
            # print mean_response_time_batches
            # print numpy.var(mean_response_time_batches)
            # print "\nboccupancy_mean_batches"
            # print boccupancy_mean_batches
            # print numpy.var(boccupancy_mean_batches)

            NUM_BATCHES = int(round(SIM_TIME/DIM_BATCHES))

            mean_response_time[x,y] = numpy.mean(mean_response_time_batches)
            conf_int_tmp = t.interval(CONF_LEVEL, NUM_BATCHES-1, mean_response_time[x,y], math.sqrt(numpy.var(mean_response_time_batches)/NUM_BATCHES))
            conf_int_rt[0,x] = abs(mean_response_time[x,y] - conf_int_tmp[0])
            conf_int_rt[1,x] = abs(mean_response_time[x,y] - conf_int_tmp[1])
            # conf_int_rt.append(t.interval(CONF_LEVEL, NUM_BATCHES-1, mean_response_time[x,y], (numpy.std(mean_response_time_batches))/math.sqrt(NUM_BATCHES)))
            # print "\nMean Response Time + Conf. Int"
            # print mean_response_time[x,y]
            # print conf_int_rt[0,x]
            # print conf_int_rt[1,x]

            boccupancy_mean.append(numpy.mean(boccupancy_mean_batches))
            conf_int_tmp = t.interval(CONF_LEVEL, NUM_BATCHES-1, boccupancy_mean[-1], math.sqrt(numpy.var(boccupancy_mean_batches)/NUM_BATCHES))
            conf_int_bo[0,x] = abs(boccupancy_mean[-1] - conf_int_tmp[0])
            conf_int_bo[1,x] = abs(boccupancy_mean[-1] - conf_int_tmp[1])
            # conf_int_bo.append(t.interval(CONF_LEVEL, NUM_BATCHES-1, boccupancy_mean[-1], (numpy.std(boccupancy_mean_batches))/math.sqrt(NUM_BATCHES)))
            # print "\nMean Buffer Occupancy + Conf. Int"
            # print boccupancy_mean[-1]
            # print conf_int_bo[0,x]
            # print conf_int_bo[1,x]
            
            ro.append(servicerate/arrivalrate)
            # print ro

            # #plot Response Time
            # fig,(series, pdf, cdf) = pyplot.subplots(3, 1)
            
            # series.plot(response_time)
            # series.set_xlabel("Sample")
            # series.set_ylabel("Response-Time")
            
            # pdf.hist(response_time, bins=100, normed= True)
            # pdf.set_xlabel("Time")
            # pdf.set_ylabel("PDF")
            # #pdf.set_xbound(0, 15)
            
            # cdf.hist(response_time, bins= 100, cumulative= True, normed= True)
            # cdf.set_xlabel("Time")
            # cdf.set_ylabel("P(Response Time <= x)")
            # cdf.set_ybound(0, 1)
            
            # #plot buffer occupancy
            # fig2,(series, pdf, cdf) = pyplot.subplots(3, 1)
            
            # series.plot(webserver.boccupancy)
            # series.set_xlabel("Sample")
            # series.set_ylabel("Buffer-Occupancy")
            
            # pdf.hist(webserver.boccupancy, bins=100, normed= True)
            # pdf.set_xlabel("Time")
            # pdf.set_ylabel("PDF")
            # #pdf.set_xbound(0, 15)
            
            # cdf.hist(webserver.boccupancy, bins= 100, cumulative= True, normed= True)
            # cdf.set_xlabel("Time")
            # cdf.set_ylabel("P(Buffer-Occupancy <= x)")
            # cdf.set_ybound(0, 1)
            
            # pyplot.show()
            y += 1
        x += 1

    print("\nSimulation ended! Plotting some results...\n")

    #plot mean response time
    fig1, responsetime_mean = pyplot.subplots(1,1)
    ci_rest = responsetime_mean.errorbar(ro, mean_response_time[:,0], xerr=0, yerr=conf_int_rt[:,:], fmt='.', color='c', label="Conf Int")
    emp_rest, = responsetime_mean.plot(ro,mean_response_time[:,0],label='Empirical')
    responsetime_mean.set_xlabel("ro")
    responsetime_mean.set_ylabel("Mean Response Time")
    responsetime_mean.grid()

    #plot mean number of customers in queueing line
    fig2, bo_mean = pyplot.subplots(1,1)
    ci_bo = bo_mean.errorbar(ro, boccupancy_mean, xerr=0, yerr=conf_int_bo[:,:], fmt='.', color='c', label="Conf Int")
    emp_bo, = bo_mean.plot(ro,boccupancy_mean, label='Empirical')
    bo_mean.set_xlabel("ro")
    bo_mean.set_ylabel("Mean Buffer Occupancy")
    bo_mean.grid()

    responsetime_mean.legend(handles=[emp_rest,ci_rest])
    bo_mean.legend(handles=[emp_bo,ci_bo])


    pyplot.show()