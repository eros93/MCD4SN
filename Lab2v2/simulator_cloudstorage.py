#!/usr/bin/python
from collections import deque
from numpy import random
from matplotlib import pyplot
import simpy
import numpy
import time


RANDOM_SEED = 7
SIM_TIME = 1000000

# max number of devices in the simulation
NUM_DEV = 201
STEP = 5


th_file = []
# number of clients connected (session_on)
devs = 0
online_devs = []
# download traffic CLOUD
instant_downtraffic = 0
downtraffic = []
# upload traffic CLOUD
instant_uptraffic = 0
uptraffic = []

# global incremental id for files
global_id = 0


#******************************************************************************
# Utility FUNCTIONS
#******************************************************************************

def get_throughput():
    global th_file
    # here we take  the throughput randomly
    while True:
        int_max_line = len(th_file)
        index_line = random.randint(1, int_max_line)
        line = th_file[index_line]
        # th [bit/sec]
        throughput_tmp = float(line.split()[1])
        if throughput_tmp > 0:
            return float(line.split()[1]) # this is the throughput

def get_random_file():
    global th_file
    # here we take  the file randomly
    int_max_line = len(th_file)
    index_line = random.randint(1, int_max_line)
    line = th_file[index_line]
    # fileSize [Byte]
    size = line.split()[0]  # this is the file size
    return File(size)

def reset_global_vars():
    global online_devs
    global downtraffic
    global uptraffic
    global devs
    global instant_uptraffic
    global instant_downtraffic
    global last_update_time
    devs = 0
    online_devs = []
    instant_downtraffic = 0
    downtraffic = []
    instant_uptraffic = 0
    uptraffic = []
    last_update_time = 0

    return

#******************************************************************************
# class representing the FILES
#******************************************************************************
class File(object):

    #constructor
    def __init__(self, size):
        global global_id

        global_id += 1
        self.id = global_id
        self.size = size

    def get_size(self):
        return int(self.size)

#******************************************************************************
# class representing the SHARED FOLDERS
#******************************************************************************
class SharedFolder(object):

    def __init__(self, id):
        self.id = id
        self.my_devices = []
        self.file = {}

    # fancy printing as string
    def __str__(self):
        return str(self.id)

    # add a device to the list of devices registering this shared folder
    def add_device(self, device):
        self.my_devices.append(device)

#******************************************************************************
# class representing DEVICES
#******************************************************************************
class Device():

    # costructor
    def __init__(self, id):
        self.id = id
        self.env = None
        self.download_queue = []
        self.my_shared_folders = [] 

    # fancy printing as string
    def __str__(self):
        sf_str = ", ".join([str(i) for i in self.my_shared_folders])
        return "Device: " + str(self.id) + ", Shared Folders [" + sf_str + "]"

    # add a shared folder to this device
    def add_shared_folder(self, sf):
        self.my_shared_folders.append(sf)

    def get_device_id(self):
        return self.id


    def download_proc(self, maxtime):
        global instant_downtraffic
        global downtraffic

        # download until the download queue is empty
        while self.download_queue :
            file = self.download_queue.pop()
            down_throughput = get_throughput()
            transfer_time = file.get_size()/(8 * down_throughput)

                # check if the time is enough to finish the download
            if maxtime > self.env.now + transfer_time:
                instant_downtraffic += down_throughput
                downtraffic.append(instant_downtraffic)
                yield self.env.timeout(transfer_time)
                instant_downtraffic -= down_throughput
                downtraffic.append(instant_downtraffic)


    def upload_proc(self,maxtime,folder):
        global instant_uptraffic
        global uptraffic

        file = get_random_file()
        up_throughput = get_throughput()
        if up_throughput == 0 :
            print "up_throughput zero!",up_throughput
        transfer_time = file.get_size() / (8 * up_throughput)
        # check if the time is enough to complete the upload
        if maxtime > self.env.now + transfer_time:
            instant_uptraffic += up_throughput
            uptraffic.append(instant_uptraffic)
            yield self.env.timeout(transfer_time)
            instant_uptraffic -= up_throughput
            uptraffic.append(instant_uptraffic)

            # put the uploaded file into the download queue of other connected devices
            for device in folder.my_devices :
                if device.get_device_id() != self.id:
                    device.download_queue.append(file)




    def session_off(self):
        # extract the duration of inter-session-time
        inter_session_time = random.lognormal(mean=7.971,sigma=1.308)
        # print (self.id,' device --> session off! @ ',self.env.now)
        yield self.env.timeout(inter_session_time)
        # print (self.id,' device has finish the session off! @ ',self.env.now)


    def session_on(self):
        # extract the duration of session
        session_time = random.lognormal(mean=8.492,sigma=1.545)
        # extract the maximum online time
        max_time = self.env.now + session_time
        # extract randomly one connected folder
        folder = random.choice(self.my_shared_folders)

        while self.env.now < max_time:
            # start download process
            yield self.env.process(self.download_proc(max_time))
            # extract and wait the time among two uploads
            inter_upload_time = random.lognormal(mean=3.748,sigma=2.286)
            yield self.env.timeout(inter_upload_time)
            yield self.env.process(self.upload_proc(max_time, folder))



    def process(self):
        global devs
        global online_devs
        global last_update_time

        while True:
            devs += 1
            #print "devices now active are: ",devs
            online_devs.append(devs)
            yield self.env.process(self.session_on())

            devs -= 1
            #print "devices now active are: ",devs
            yield self.env.process(self.session_off())
            online_devs.append(devs)


#******************************************************************************
# Create the synthetic content synchronization network
#******************************************************************************
def generate_network(num_dv, devices, shared_folders):

    # shared folders per device - negative_binomial (s, mu)
    DV_DG = [0.470, 1.119]

    # device per shared folder - negative_binomial (s, mu)
    SF_DG = [0.231, 0.537]

    # derive the expected number of shared folders using the negative_binomials

    # this piece is just converting the parameterization of the
    # negative_binomials from (s, mu) to "p". Then, we use the rate between
    # the means to estimate the expected number of shared folders
    # from the given number of devices

    dv_s = DV_DG[0]
    dv_m = DV_DG[1]
    dv_p = dv_s / (dv_s + dv_m)
    nd = 1 + (dv_s * (1.0 - dv_p) / dv_p)

    sf_s = SF_DG[0]
    sf_m = SF_DG[1]
    sf_p = sf_s / (sf_s + sf_m)
    dn = 1 + (sf_s * (1.0 - sf_p) / sf_p)

    # the number of shared folders is finally derived
    num_sf = int(num_dv * nd / dn)

    # sample the number of devices per shared folder (shared folder degree)
    sf_dgr = [x + 1 for x in random.negative_binomial(sf_s, sf_p, num_sf)]

    # sample the number of shared folders per device (device degree)
    dv_dgr = [x + 1 for x in random.negative_binomial(dv_s, dv_p, num_dv)]

    # create the population of edges leaving shared folders
    l = [i for i, j in enumerate(sf_dgr) for k in range(min(j, num_dv))]
    random.shuffle(l)
    sf_pop = deque(l)

    # create empty shared folders
    for sf_id in range(num_sf):
        shared_folders[sf_id] = SharedFolder(sf_id)

    # first we pick a random shared folder for each device
    for dv_id in range(num_dv):
        devices[dv_id] = Device(dv_id)

        sf_id = sf_pop.pop()
        devices[dv_id].add_shared_folder(shared_folders[sf_id])
        shared_folders[sf_id].add_device(devices[dv_id])

    # then we complement the shared folder degree

    # we skip devices with degree 1 in a first pass, since they just got 1 sf
    r = 1

    # we might have less edges leaving devices than necessary
    while sf_pop:
        # create the population of edges leaving devices
        l = [i for i, j in enumerate(dv_dgr) for k in range(min(j - r, num_sf))]
        random.shuffle(l)
        dv_pop = deque(l)

        # if we need to recreate the population, we use devices w/ degree 1 too
        r = 0

        while sf_pop and dv_pop:
            dv = dv_pop.pop()
            sf = sf_pop.pop()

            # we are lazy and simply skip the unfortunate repetitions
            if not shared_folders[sf] in devices[dv].my_shared_folders:
                devices[dv].add_shared_folder(shared_folders[sf])
                shared_folders[sf].add_device(devices[dv])
            else:
                sf_pop.append(sf)






#******************************************************************************
# SIMULATION
#******************************************************************************
if __name__ == '__main__':

    # read the file THROUGHPUT.txt
    f = open("throughput.txt", "r")
    th_file = f.readlines()
    f.close()

    mean_active_devs = []
    mean_download_trf = []
    mean_upload_trf = []

    for N in range(5,NUM_DEV,STEP): 

        # reset the global variables for a new run
        reset_global_vars()

        # collection of devices
        devices = {}

        # collection of shared folders
        shared_folders = {}

        # set the random seed
        random.seed(RANDOM_SEED)

        # create the content sharing network
        generate_network(N, devices, shared_folders)

        # generates the environment (equal for all the elements in simulation)
        env = simpy.Environment()

        # DEBUG: dumping the network
        # for dev_id in devices:
        #     print str(devices[dev_id])

        for dev_id in devices:
            devices[dev_id].env = env
            env.process(devices[dev_id].process())

        env.run(until=SIM_TIME)

        # Statistics

        mean_active_devs.append(numpy.mean(online_devs))
        mean_download_trf.append(numpy.mean(downtraffic))
        mean_upload_trf.append(numpy.mean(uptraffic))

        # print "Mean # of active devices: ", numpy.mean(online_devs)
        # print "Mean download traffic: ", numpy.mean(downtraffic)
        # print "Mean upload traffic: ", numpy.mean(uptraffic)

        # fig, (active_devices, download_trf, upload_trf) = pyplot.subplots(3,1)

        # active_devices.plot(online_devs)
        # active_devices.set_ylabel("Number of ACTIVE devices")

        # download_trf.plot(downtraffic)
        # download_trf.set_ylabel("Download traffic")

        # upload_trf.plot(uptraffic)
        # upload_trf.set_ylabel("Upload traffic")


        # pyplot.figure(2)
        # pyplot.hist(online_devs, bins=100)
        # pyplot.figure(3)
        # pyplot.hist(uptraffic, bins=100)

        # pyplot.show()

    print mean_active_devs
    print mean_download_trf
    print mean_upload_trf
    fig, (active_devices, download_trf, upload_trf) = pyplot.subplots(3,1)
    num = numpy.linspace(2, NUM_DEV, len(mean_active_devs))
    active_devices.plot(num, mean_active_devs)
    active_devices.set_xlabel("N - Number of devices")
    active_devices.set_ylabel("Mean # of ACTIVE devices")
    
    del num
    num = numpy.linspace(2, NUM_DEV, len(mean_download_trf))
    download_trf.plot(num, mean_download_trf)
    download_trf.set_xlabel("N - Number of devices")
    download_trf.set_ylabel("Mean Download traffic")
    
    del num
    num = numpy.linspace(2, NUM_DEV, len(mean_upload_trf))
    upload_trf.plot(num, mean_upload_trf)
    upload_trf.set_xlabel("N - Number of devices")
    upload_trf.set_ylabel("Mean Upload traffic")

    pyplot.show()
