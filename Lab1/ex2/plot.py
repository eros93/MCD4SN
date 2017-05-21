import json
import numpy
from matplotlib import pyplot

# Data Source File
FILENAME = "results/simulation_result_170521_1108.json"


if __name__ == '__main__':

	# READING data from file
	inputfile = open(FILENAME,"r")
	inputdata = json.loads(inputfile.read())
	inputfile.close()

	NUM = inputdata["NUM"]
	RANDOM_SEED = inputdata["RANDOM_SEED"]
	SERVICE_TIME1 = inputdata["SERVICE_TIME1"]
	SERVICE_TIME2 = inputdata["SERVICE_TIME2"]
	ARRIVAL_TIME = inputdata["ARRIVAL_TIME"]
	buffer1 = inputdata["buffer1"]
	buffer2 = inputdata["buffer2"]
	A = inputdata["minbatch"]
	B = inputdata["maxbatch"]
	CONF_LEVEL = inputdata["CONF_LEVEL"]
	SIM_TIME = inputdata["SIM_TIME"]
	DIM_BATCHES = inputdata["DIM_BATCHES"]
	NUM_BATCHES = inputdata["NUM_BATCHES"]
	mean_response_time = inputdata["mean_response_time"]
	ci_rt = inputdata["conf_int_rt"]
	boccupancy1_mean = inputdata["boccupancy1_mean"]
	ci_bo1 = inputdata["conf_int_bo1"]
	boccupancy2_mean = inputdata["boccupancy2_mean"]
	ci_bo2 = inputdata["conf_int_bo2"]

	print "\nFile correctly read.\n"

	print("""
	File in use: %r.
	Main DATA:
	\t- Simulation Time = %r
	\t- # of Batches (SIMULATION): %r (dimension = %r)
	\t- Arrival time = %r
	\t- Service time Front End = %r
	\t- Service time Back End = %r
	\t- Packet batch: min=%r / max=%r (uniform distr.)
	\t- Buffer Front End = %r 
	\t- Buffer Back End = %r
	""" %(FILENAME, SIM_TIME, NUM_BATCHES, DIM_BATCHES, ARRIVAL_TIME, SERVICE_TIME1, SERVICE_TIME2, A, B, buffer1, buffer2))

	ans = raw_input("\n\t---> Would you like to plot the results? [Y/N]\t").lower()
	if ans != "y":
		plotflag = 0
		quit()


	# Filling confidence_intervals lists
	conf_int_rt = numpy.zeros((2,NUM))
	conf_int_bo1 = numpy.zeros((2,NUM))
	conf_int_bo2 = numpy.zeros((2,NUM))

	conf_int_rt[0,:] = ci_rt
	conf_int_rt[1,:] = ci_rt

	conf_int_bo1[0,:] = ci_bo1
	conf_int_bo1[1,:] = ci_bo1

	conf_int_bo2[0,:] = ci_bo2
	conf_int_bo2[1,:] = ci_bo2


	print "\n\nPlotting some results..."

	#---------------------------------------------------#
	# PLOTs varying ARRIVAL TIME
	#---------------------------------------------------#
	# - plot mean response time
	fig1, responsetime_mean = pyplot.subplots(1,1)
	ci_rest = responsetime_mean.errorbar(ARRIVAL_TIME, mean_response_time, xerr=0, yerr=conf_int_rt[:,:], fmt='.', color='c', label="Conf Int")
	emp_rest, = responsetime_mean.plot(ARRIVAL_TIME, mean_response_time, label='Empirical')
	responsetime_mean.set_xlabel("Arrival Time")
	responsetime_mean.set_ylabel("Mean Response Time")
	responsetime_mean.grid()

	# - plot mean number of customers in queueing line of FRONT END
	fig2, bo_mean1 = pyplot.subplots(1,1)
	ci_bo1 = bo_mean1.errorbar(ARRIVAL_TIME, boccupancy1_mean, xerr=0, yerr=conf_int_bo1[:,:], fmt='.', color='c', label="Conf Int")
	emp_bo1, = bo_mean1.plot(ARRIVAL_TIME, boccupancy1_mean, label='Empirical')
	bo_mean1.set_xlabel("Arrival Time")
	bo_mean1.set_ylabel("Mean Buffer Occupancy")
	bo_mean1.grid()

	# - plot mean number of customers in queueing line of BACK END
	fig3, bo_mean2 = pyplot.subplots(1,1)
	ci_bo2 = bo_mean2.errorbar(ARRIVAL_TIME, boccupancy2_mean, xerr=0, yerr=conf_int_bo2[:,:], fmt='.', color='c', label="Conf Int")
	emp_bo2, = bo_mean2.plot(ARRIVAL_TIME, boccupancy2_mean, label='Empirical')
	bo_mean2.set_xlabel("Arrival Time")
	bo_mean2.set_ylabel("Mean Buffer Occupancy")
	bo_mean2.grid()

	responsetime_mean.legend(handles=[emp_rest,ci_rest])
	bo_mean1.legend(handles=[emp_bo1,ci_bo1])
	bo_mean2.legend(handles=[emp_bo2,ci_bo2])

	fig1.suptitle('Mean Response Time of system - Varying ARRIVAL_TIME')
	fig2.suptitle('Mean Buffer Occupancy FrontEnd - Varying ARRIVAL_TIME')
	fig3.suptitle('Mean Buffer Occupancy BackEnd - Varying ARRIVAL_TIME')
	pyplot.show()


	# #---------------------------------------------------#
	# # PLOTs varying SERVICE TIME FRONTEND
	# #---------------------------------------------------#
	# # - plot mean response time
	# fig1, responsetime_mean = pyplot.subplots(1,1)
	# ci_rest = responsetime_mean.errorbar(SERVICE_TIME1, mean_response_time, xerr=0, yerr=conf_int_rt[:,:], fmt='.', color='c', label="Conf Int")
	# emp_rest, = responsetime_mean.plot(SERVICE_TIME1, mean_response_time, label='Empirical')
	# responsetime_mean.set_xlabel("FrontEnd Service Time")
	# responsetime_mean.set_ylabel("Mean Response Time")
	# responsetime_mean.grid()

	# # - plot mean number of customers in queueing line of FRONT END
	# fig2, bo_mean1 = pyplot.subplots(1,1)
	# ci_bo1 = bo_mean1.errorbar(SERVICE_TIME1, boccupancy1_mean, xerr=0, yerr=conf_int_bo1[:,:], fmt='.', color='c', label="Conf Int")
	# emp_bo1, = bo_mean1.plot(SERVICE_TIME1, boccupancy1_mean, label='Empirical')
	# bo_mean1.set_xlabel("FrontEnd Service Time")
	# bo_mean1.set_ylabel("Mean Buffer Occupancy FrontEnd")
	# bo_mean1.grid()

	# # - plot mean number of customers in queueing line of BACK END
	# fig3, bo_mean2 = pyplot.subplots(1,1)
	# ci_bo2 = bo_mean2.errorbar(SERVICE_TIME1, boccupancy2_mean, xerr=0, yerr=conf_int_bo2[:,:], fmt='.', color='c', label="Conf Int")
	# emp_bo2, = bo_mean2.plot(SERVICE_TIME1, boccupancy2_mean, label='Empirical')
	# bo_mean2.set_xlabel("FrontEnd Service Time")
	# bo_mean2.set_ylabel("Mean Buffer Occupancy BackEnd")
	# bo_mean2.grid()

	# responsetime_mean.legend(handles=[emp_rest,ci_rest])
	# bo_mean1.legend(handles=[emp_bo1,ci_bo1])
	# bo_mean2.legend(handles=[emp_bo2,ci_bo2])

	# fig1.suptitle('Mean Response Time - Varying SERVICE_TIME1')
	# fig2.suptitle('Mean Buffer Occupancy FrontEnd - Varying SERVICE_TIME1')
	# fig3.suptitle('Mean Buffer Occupancy BackEnd - Varying SERVICE_TIME1')
	# pyplot.show()


	# #---------------------------------------------------#
	# # PLOTs varying SERVICE TIME BACKEND
	# #---------------------------------------------------#
	# # - plot mean response time
	# fig1, responsetime_mean = pyplot.subplots(1,1)
	# ci_rest = responsetime_mean.errorbar(SERVICE_TIME2, mean_response_time, xerr=0, yerr=conf_int_rt[:,:], fmt='.', color='c', label="Conf Int")
	# emp_rest, = responsetime_mean.plot(SERVICE_TIME2, mean_response_time, label='Empirical')
	# responsetime_mean.set_xlabel("BackEnd Service Time")
	# responsetime_mean.set_ylabel("Mean Response Time")
	# responsetime_mean.grid()

	# # - plot mean number of customers in queueing line of FRONT END
	# fig2, bo_mean1 = pyplot.subplots(1,1)
	# ci_bo1 = bo_mean1.errorbar(SERVICE_TIME2, boccupancy1_mean, xerr=0, yerr=conf_int_bo1[:,:], fmt='.', color='c', label="Conf Int")
	# emp_bo1, = bo_mean1.plot(SERVICE_TIME2, boccupancy1_mean, label='Empirical')
	# bo_mean1.set_xlabel("BackEnd Service Time")
	# bo_mean1.set_ylabel("Mean Buffer Occupancy FrontEnd")
	# bo_mean1.grid()

	# # - plot mean number of customers in queueing line of BACK END
	# fig3, bo_mean2 = pyplot.subplots(1,1)
	# ci_bo2 = bo_mean2.errorbar(SERVICE_TIME2, boccupancy2_mean, xerr=0, yerr=conf_int_bo2[:,:], fmt='.', color='c', label="Conf Int")
	# emp_bo2, = bo_mean2.plot(SERVICE_TIME2, boccupancy2_mean, label='Empirical')
	# bo_mean2.set_xlabel("BackEnd Service Time")
	# bo_mean2.set_ylabel("Mean Buffer Occupancy BackEnd")
	# bo_mean2.grid()

	# responsetime_mean.legend(handles=[emp_rest,ci_rest])
	# bo_mean1.legend(handles=[emp_bo1,ci_bo1])
	# bo_mean2.legend(handles=[emp_bo2,ci_bo2])

	# fig1.suptitle('Mean Response Time - Varying SERVICE_TIME2')
	# fig2.suptitle('Mean Buffer Occupancy FrontEnd - Varying SERVICE_TIME2')
	# fig3.suptitle('Mean Buffer Occupancy BackEnd - Varying SERVICE_TIME2')
	# pyplot.show()