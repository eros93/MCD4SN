import simpy
import random
import numpy
from matplotlib import pyplot

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
# CONSTANTS
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
RANDOM_SEED = 7

#SERVICE_RATE = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
#ARRIVAL_RATE = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
NUM = 100

SERVICE_TIME = [2.0] # it is the inverse of the service rate (speed)
ARRIVAL_TIME = [8.0]
#SERVICE_RATE = numpy.linspace(1.0, 10.0, num = NUM)
#ARRIVAL_RATE = numpy.linspace(1.0, 10.0, num = NUM)


NUM_SERVER = 1
SIM_TIME = 100000

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
# WEB SERVER Class
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
class WebServer(object):

    def __init__(self, environ, numserver, service_rate):

        # define the number of servers in parallel
        self.servers = simpy.Resource(environ, numserver)

        # holds samples of request-processing time
        self.service_time = []

        self.service_rate = service_rate
        self.env = environ
        self.instant_boccupancy = 0
        self.instant_qsize = 0
        self.boccupancy = []
        self.qsize = []

    def service_process(self):

        self.instant_qsize += 1

        # make a server request
        with self.servers.request() as request:
            self.instant_boccupancy += 1
            #print ("Request has required the resource at ", self.env.now)
            yield request
            self.instant_boccupancy -= 1
            #print ("Request has received the resource at ", self.env.now)

            # once the servers is free, wait until service is finished
            service_time = random.expovariate(lambd=1.0/self.service_rate)
            self.boccupancy.append(self.instant_boccupancy)
            # yield an event to the simulator
            yield self.env.timeout(service_time)
            self.service_time.append(self.env.now)
            self.instant_qsize -= 1
            self.qsize.append(self.instant_qsize)


            #print ("Request satisfied at ", self.env.now)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
# REQUEST Class
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
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
            inter_arrival = random.expovariate(lambd=1.0/self.arrival_rate)

            # yield an event to the simulator
            yield self.env.timeout(inter_arrival)
            self.inter_arrival.append(self.env.now)    # sample time of arrival

            # a request has arrived - request the service to the server
            #print ("Request has arrived at ", self.env.now)
            self.env.process(web_service.service_process())

#----------------------------------------------------------------------------------------------#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
# MAIN
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

if __name__ == '__main__':

    print("Starting the simulation... ")

    txt=open("result_simulation.txt","w+")
    txt.truncate()

    matrix = [[0 for x in range(NUM)] for y in range(NUM)]

    x = 0
    for servicerate in SERVICE_TIME:
        y = 0
        for arrivalrate in ARRIVAL_TIME:

            random.seed(RANDOM_SEED)

            env = simpy.Environment()

            # arrival
            request = RequestArrival(env, arrivalrate)

            # web service
            webserver = WebServer(env, NUM_SERVER, servicerate)

            # starts the arrival process
            env.process(request.arrival_process(webserver))

            # simulate until SIM_TIME
            env.run(until= SIM_TIME)


            # Statistics
            txt.write("Arrival rate [lambda]: %f - Service rate [u]: %f \n" %(arrivalrate, servicerate))
            txt.write("Number of requests: %d \t" %len(request.inter_arrival))
            txt.write("Number of requests satisfied: %d \n" %len(webserver.service_time))
            txt.write("Number of requests not satisfied: %d \n" % (len(request.inter_arrival) - len(webserver.service_time)))

            # truncate inter_arrival list when not all are satisfied
            del request.inter_arrival[(len(webserver.service_time)):]

            # Calculate Vector of response time
            response_time = [i[0] - i[1] for i in zip(webserver.service_time, request.inter_arrival)]
            matrix[x][y] = numpy.mean(response_time)
            
            txt.write("Average RESPONSE TIME for requests: %f" %matrix[x][y])
            txt.write("\n\n")

            #plot
            fig,(series, pdf, cdf) = pyplot.subplots(3, 1)

            series.plot(response_time)
            series.set_xlabel("Sample")
            series.set_ylabel("Response-Time")
            pyplot.show()

            y += 1
        x += 1

    print("Simulation ended! Plotting some results...")

