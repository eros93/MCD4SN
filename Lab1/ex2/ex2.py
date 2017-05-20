import simpy
import random
import numpy
from matplotlib import pyplot
from scipy.stats import t
import math
import json

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
# CONSTANTS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
RANDOM_SEED = 7

# SERVICE_RATE = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
# ARRIVAL_RATE = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
NUM = 25

#FIXED
#SERVICE_TIME1 = 2.0 #[Front-End] it is the inverse of the service rate (speed)
#SERVICE_TIME2 = 4.0 #[Back-End]
#ARRIVAL_TIME = 4.0

#VARYING arrival_time
SERVICE_TIME1 = 2.0
SERVICE_TIME2 = 5.0
ARRIVAL_TIME = numpy.linspace(1.0, 10.0, num = NUM)
#ARRIVAL_TIME = [float(z) for z in numpy.linspace(1.0, 10.0, num = NUM)]

# Batch dimension
A = 1   # MAX
B = 5   # MIN

# Buffers dimension
B1 = 10000   # Front-end
B2 = 10000   # Back-end

# Probability of reqs not satisfied by Front End
P = 0.25

CONF_LEVEL = 0.9
DIM_BATCHES = 50000

NUM_SERVER = 1
SIM_TIME = 1500000


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
# WEB SERVER Class
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

class WebServer(object):
    def __init__(self, environ, numserver, qcapacity1, qcapacity2, service_rate1, service_rate2):
        
        # define the number of servers in parallel
        self.frontEnd = simpy.Resource(environ, numserver)
        self.backEnd = simpy.Resource(environ, numserver)

        self.service_rate1 = service_rate1
        self.service_rate2 = service_rate2

        self.env = environ

        # Holds samples of request-processing time
        self.service_time = []

        self.instant_qsize = 0
        self.qsize = []

        #Front-end stuffs
        self.instant_boccupancy1 = 0
        self.boccupancy1 = []

        self.qcapacity1 = qcapacity1
        self.discarded1 = 0

        #Back-end stuffs
        self.instant_boccupancy2 = 0
        self.boccupancy2 = []

        self.qcapacity2 = qcapacity2
        self.discarded2 = 0

    @property
    def service_process(self):
        self.instant_qsize += 1

        if (self.instant_boccupancy1 <= self.qcapacity1):
            # make a server request
            with self.frontEnd.request() as frontRequest:
                self.instant_boccupancy1 += 1
                #  print ("Request has required the resource 1 at ", self.env.now)
                yield frontRequest
                self.instant_boccupancy1 -= 1
                # print ("Request has *** received the resource 1 at ", self.env.now)

                # once the servers is free, wait until service is finished
                service_time1 = random.expovariate(lambd=1.0/self.service_rate1)
                self.boccupancy1.append(self.instant_boccupancy1)
                # yield an event to the simulator
                yield self.env.timeout(service_time1)

                coin = numpy.random.random()
        else:
            self.discarded1 += 1
            return
            #print "A FrontEnd request was discarded"
            #  print ("Request satisfied at ", self.env.now)

        if (coin < P):

            if (self.instant_boccupancy2 <= self.qcapacity2):
                # make a server request
                with self.backEnd.request() as backRequest:
                    self.instant_boccupancy2 += 1
                    #print ("Request has required the resource 2 at ", self.env.now)
                    yield backRequest
                    self.instant_boccupancy2 -= 1
                    #print ("Request has *** received the resource 2 at ", self.env.now)

                    # once the servers is free, wait until service is finished
                    service_time2 = random.expovariate(lambd=1.0 / self.service_rate2)
                    self.boccupancy2.append(self.instant_boccupancy2)
                    # yield an event to the simulator
                    #print service_time2
                    yield self.env.timeout(service_time2)
                    self.service_time.append(self.env.now)
                    self.instant_qsize -= 1
                    self.qsize.append(self.instant_qsize)
            else:
                self.discarded2 += 1
                #print "A BackEnd request was discarded"
                return
        else:
            self.service_time.append(self.env.now)
            self.instant_qsize -= 1
            self.qsize.append(self.instant_qsize)


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
                #print "Front_End request number : %d is finished " %(i+1)

                # coin = numpy.random.random()
                # if (coin < P):
                #     #print coin
                #     self.env.process(web_service2.service_process)
                #     #web_service1.service_time[-1] = web_service2.service_time[-1] #insert the correct service time for that req
                #     #print "Back_End request number : %d is finished " % (i+1)




# ----------------------------------------------------------------------------------------------#
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
# MAIN
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


if __name__ == '__main__':

    random.seed(RANDOM_SEED)

    print("Starting the simulation... ")

    mean_response_time = []
    #mean_response_time = numpy.zeros((NUM,NUM))
    conf_int_rt = numpy.zeros((2,NUM))

    boccupancy1_mean = []
    conf_int_bo1 = numpy.zeros((2,NUM))

    boccupancy2_mean = []
    conf_int_bo2 = numpy.zeros((2,NUM))

    #ro = []    # NOT USED in this simulation

    x = 0
    y = 0
    
    for arrivalrate in ARRIVAL_TIME:

        env = simpy.Environment()

        # Arrival of Batches
        arrival = RequestArrival(env, arrivalrate)

        # Web Server (Front-end + Back-end)
        webserver = WebServer(env, NUM_SERVER, B1, B2, SERVICE_TIME1,SERVICE_TIME2)

        # Starts the arrival process
        env.process(arrival.arrival_process(webserver))

        # Batches analysis

        #Reset the data structures
        pointer_rt = 0
        pointer_bo1 = 0
        pointer_bo2 = 0
        mean_response_time_batches = []
        boccupancy1_mean_batches = []
        boccupancy2_mean_batches = []


        for index in range(1,(SIM_TIME/DIM_BATCHES)+1):
            # simulate until index*DIM_BATCHES
            env.run(until = index*DIM_BATCHES)

            # Statistics

            # take only the datas related to the one processed in the batch
            inter_arrival_batch = arrival.inter_arrival[ pointer_rt : len(webserver.service_time) ]
            service_time_batch = webserver.service_time[ pointer_rt : ]
            
            boccupancy1_batch = webserver.boccupancy1[ pointer_bo1 : ]
            boccupancy2_batch = webserver.boccupancy2[ pointer_bo2 : ]

            # update pointer index
            pointer_rt = len(webserver.service_time)
            pointer_bo1 = len(webserver.boccupancy1)
            pointer_bo2 = len(webserver.boccupancy2)

            # Calculate Vector of Response Times for the batch
            response_time = [ i[0] - i[1] for i in zip(service_time_batch, inter_arrival_batch) ]

            # Mean values estimation
            # Response Time
            batch_mean = numpy.mean(response_time)
            mean_response_time_batches.append(batch_mean)
            
            # Buffer Occupancy
            # 1 [Front-End]
            batch_mean = numpy.mean(boccupancy1_batch)
            boccupancy1_mean_batches.append(batch_mean)
            # 2 [Back-End]
            batch_mean = numpy.mean(boccupancy2_batch)
            boccupancy2_mean_batches.append(batch_mean)


        # print "\nmean_response_time_batches"
        # print mean_response_time_batches
        # print numpy.var(mean_response_time_batches)
        # print "\nboccupancy1_mean_batches"
        # print boccupancy1_mean_batches
        # print numpy.var(boccupancy1_mean_batches)
        # print "\nboccupancy2_mean_batches"
        # print boccupancy2_mean_batches
        # print numpy.var(boccupancy2_mean_batches)


        NUM_BATCHES = int(round(SIM_TIME/DIM_BATCHES))

        mean_response_time.append(numpy.mean(mean_response_time_batches))
        conf_int_tmp = t.interval(CONF_LEVEL, NUM_BATCHES-1, mean_response_time[-1], math.sqrt(numpy.var(mean_response_time_batches)/NUM_BATCHES))
        conf_int_rt[0,x] = abs(mean_response_time[-1] - conf_int_tmp[0])
        conf_int_rt[1,x] = abs(mean_response_time[-1] - conf_int_tmp[1])
        # conf_int_rt.append(t.interval(CONF_LEVEL, NUM_BATCHES-1, mean_response_time[x,y], (numpy.std(mean_response_time_batches))/math.sqrt(NUM_BATCHES)))
        # print "\nMean Response Time + Conf. Int"
        # print mean_response_time[x,y]
        # print conf_int_rt[0,x]
        # print conf_int_rt[1,x]

        boccupancy1_mean.append(numpy.mean(boccupancy1_mean_batches))
        conf_int_tmp = t.interval(CONF_LEVEL, NUM_BATCHES-1, boccupancy1_mean[-1], math.sqrt(numpy.var(boccupancy1_mean_batches)/NUM_BATCHES))
        conf_int_bo1[0,x] = abs(boccupancy1_mean[-1] - conf_int_tmp[0])
        conf_int_bo1[1,x] = abs(boccupancy1_mean[-1] - conf_int_tmp[1])
        # conf_int_bo.append(t.interval(CONF_LEVEL, NUM_BATCHES-1, boccupancy_mean[-1], (numpy.std(boccupancy_mean_batches))/math.sqrt(NUM_BATCHES)))
        # print "\nMean Buffer Occupancy + Conf. Int"
        # print boccupancy1_mean[-1]
        # print conf_int_bo1[0,x]
        # print conf_int_bo1[1,x]

        boccupancy2_mean.append(numpy.mean(boccupancy2_mean_batches))
        conf_int_tmp = t.interval(CONF_LEVEL, NUM_BATCHES-1, boccupancy2_mean[-1], math.sqrt(numpy.var(boccupancy2_mean_batches)/NUM_BATCHES))
        conf_int_bo2[0,x] = abs(boccupancy2_mean[-1] - conf_int_tmp[0])
        conf_int_bo2[1,x] = abs(boccupancy2_mean[-1] - conf_int_tmp[1])
        # print boccupancy2_mean[-1]
        # print conf_int_bo2[0,x]
        # print conf_int_bo2[1,x]


        # #DEBUG
        # print "\n\n- Number of requests: %d" %len(arrival.inter_arrival)
        # print "- Number of served request: %d" %len(webserver.service_time)
        
        # print "- Front end discarded: %d " %webserver.discarded1
        # print "- Back end discarded: %d " %webserver.discarded2

        # print "- Processed + Discarded: %d" %(len(webserver.service_time)+webserver.discarded1+webserver.discarded2) 

        # # PLOT Response Time
        # fig,(series, pdf, cdf) = pyplot.subplots(3, 1)

        # series.plot(response_time)
        # series.set_xlabel("Sample")
        # series.set_ylabel("Overall Response-Time")

        # pdf.hist(response_time, bins=100, normed= True)
        # pdf.set_xlabel("Time")
        # pdf.set_ylabel("PDF")
        # #pdf.set_xbound(0, 15)

        # cdf.hist(response_time, bins= 100, cumulative= True, normed= True)
        # cdf.set_xlabel("Time")
        # cdf.set_ylabel("P(Response Time <= x)")
        # cdf.set_ybound(0, 1)

        # # PLOT buffer occupancy FrontEnd
        # fig2,(series, pdf, cdf) = pyplot.subplots(3, 1)

        # series.plot(webserver.boccupancy1)
        # series.set_xlabel("Sample")
        # series.set_ylabel("FrontEnd Buffer-Occupancy")

        # pdf.hist(webserver.boccupancy1, bins=100, normed= True)
        # pdf.set_xlabel("Time")
        # pdf.set_ylabel("PDF")
        # #pdf.set_xbound(0, 15)

        # cdf.hist(webserver.boccupancy1, bins= 100, cumulative= True, normed= True)
        # cdf.set_xlabel("Time")
        # cdf.set_ylabel("P(Buffer-Occupancy <= x)")
        # cdf.set_ybound(0, 1)

        # # PLOT buffer occupancy BackEnd
        # fig3,(series, pdf, cdf) = pyplot.subplots(3, 1)

        # series.plot(webserver.boccupancy2)
        # series.set_xlabel("Sample")
        # series.set_ylabel("BackEnd Buffer-Occupancy")

        # pdf.hist(webserver.boccupancy2, bins=100, normed= True)
        # pdf.set_xlabel("Time")
        # pdf.set_ylabel("PDF")
        # #pdf.set_xbound(0, 15)

        # cdf.hist(webserver.boccupancy2, bins= 100, cumulative= True, normed= True)
        # cdf.set_xlabel("Time")
        # cdf.set_ylabel("P(Buffer-Occupancy <= x)")
        # cdf.set_ybound(0, 1)

        # pyplot.show()
        x += 1

    print("\nSimulation ended! Saving and Plotting some results...\n")


    # SAVE DATA [CHANGE NAME depending on which is let varying]
    txt=open("simulation_result.json","w+")
    txt.truncate()

    output = {}
    output["RANDOM_SEED"] = RANDOM_SEED
    output["SERVICE_TIME1"] = SERVICE_TIME1
    output["SERVICE_TIME2"] = SERVICE_TIME2
    output["ARRIVAL_TIME"] = [float(z) for z in ARRIVAL_TIME]
    output["buffer1"] = B1
    output["buffer2"] = B2
    output["minbatch"] = A
    output["maxbatch"] = B
    output["CONF_LEVEL"] = CONF_LEVEL
    output["mean_response_time"] = mean_response_time
    output["conf_int_rt"] = [float(z) for z in conf_int_rt[0,:]]
    output["boccupancy1_mean"] = boccupancy1_mean
    output["conf_int_bo1"] = [float(z) for z in conf_int_bo1[0,:]]
    output["boccupancy2_mean"] = boccupancy2_mean
    output["conf_int_bo2"] = [float(z) for z in conf_int_bo2[0,:]]

    txt.write(json.dumps(output))
    txt.close()


    # # VARYING ARRIVAL TIME
    # #plot mean response time
    # fig1, responsetime_mean = pyplot.subplots(1,1)
    # ci_rest = responsetime_mean.errorbar(ARRIVAL_TIME, mean_response_time, xerr=0, yerr=conf_int_rt[:,:], fmt='.', color='c', label="Conf Int")
    # emp_rest, = responsetime_mean.plot(ARRIVAL_TIME, mean_response_time, label='Empirical')
    # responsetime_mean.set_xlabel("Arrival Time")
    # responsetime_mean.set_ylabel("Mean Response Time")
    # responsetime_mean.grid()

    # #plot mean number of customers in queueing line of FRONT END
    # fig2, bo_mean1 = pyplot.subplots(1,1)
    # ci_bo1 = bo_mean1.errorbar(ARRIVAL_TIME, boccupancy1_mean, xerr=0, yerr=conf_int_bo1[:,:], fmt='.', color='c', label="Conf Int")
    # emp_bo1, = bo_mean1.plot(ARRIVAL_TIME, boccupancy1_mean, label='Empirical')
    # bo_mean1.set_xlabel("Arrival Time")
    # bo_mean1.set_ylabel("Mean Buffer Occupancy FrontEnd")
    # bo_mean1.grid()

    # #plot mean number of customers in queueing line of BACK END
    # fig2, bo_mean2 = pyplot.subplots(1,1)
    # ci_bo2 = bo_mean2.errorbar(ARRIVAL_TIME, boccupancy2_mean, xerr=0, yerr=conf_int_bo2[:,:], fmt='.', color='c', label="Conf Int")
    # emp_bo2, = bo_mean2.plot(ARRIVAL_TIME, boccupancy2_mean, label='Empirical')
    # bo_mean2.set_xlabel("Arrival Time")
    # bo_mean2.set_ylabel("Mean Buffer Occupancy BackEnd")
    # bo_mean2.grid()

    # responsetime_mean.legend(handles=[emp_rest,ci_rest])
    # bo_mean1.legend(handles=[emp_bo1,ci_bo1])
    # bo_mean2.legend(handles=[emp_bo2,ci_bo2])


    # pyplot.show()