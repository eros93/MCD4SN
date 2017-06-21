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
NUM_DEV = 100

th_file = []
# number of clients connected (session_on)
devs = 0
online_devs = []
instant_cloud_downtraffic = 0
cloud_downtraffic = []
instant_cloud_uptraffic = 0
cloud_uptraffic = []
instant_p2p_traffic = 0
p2p_traffic = []
# global incremental id for files
global_id = 0


# ******************************************************************************
# Utility FUNCTIONS
# ******************************************************************************

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
			return float(line.split()[1])  # this is the throughput


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
	global devs
	global instant_cloud_uptraffic
	global cloud_uptraffic
	global instant_cloud_downtraffic
	global cloud_downtraffic
	global instant_p2p_traffic
	global p2p_traffic


	devs = 0
	online_devs = []
	instant_cloud_uptraffic = 0
	cloud_uptraffic = []
	instant_cloud_downtraffic = 0
	cloud_downtraffic = []
	instant_p2p_traffic = 0
	p2p_traffic = []


	return

# ******************************************************************************
# class representing the FILES
# ******************************************************************************
class File(object):
	# constructor
	def __init__(self, size):
		global global_id

		global_id += 1
		self.id = global_id
		self.size = size
		self.my_folders = []

	def get_size(self):
		return int(self.size)


# ******************************************************************************
# class representing the SHARED FOLDERS
# ******************************************************************************
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


# ******************************************************************************
# class representing DEVICES
# ******************************************************************************
class Device():
	# costructor
	def __init__(self, id):
		self.id = id
		self.env = None
		self.logout_time = 0
		self.download_queue = []
		self.my_shared_folders = []
		self.downloaded_files = []
		self.individual_uptraffic = []
		self.individual_downtraffic = []
		self.individual_uptraffic.append(0)
		self.individual_downtraffic.append(0)
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
		global instant_cloud_downtraffic
		global cloud_downtraffic
		global instant_p2p_traffic
		global p2p_traffic

		# download until the download queue is empty
		while self.download_queue:
			server_flag = True
			file = self.download_queue.pop()
			down_throughput = get_throughput()
			transfer_time = file.get_size() / (8 * down_throughput)

			# check if the time is enough to finish the download
			if maxtime > self.env.now + transfer_time:
				# take 1 folder containing the file
				folder = file.my_folders[-1]
				# check if there are device containing that folder
				if folder.my_devices:
					# take 1 peer at time
					for peer in folder.my_devices:
						# check if the peer has that file
						if file in peer.downloaded_files:
							# check if the peer has enough time to transfer that file, if not try with another one
							if peer.logout_time < self.env.now + transfer_time:
								# check if i have enough remaining time before log out
								if maxtime > self.env.now + transfer_time:
									# take individual statistics
									self.individual_downtraffic.append(self.individual_downtraffic[-1] + down_throughput)
									peer.individual_uptraffic.append(peer.individual_uptraffic[-1] + down_throughput)
									# take global p2p statistics
									instant_p2p_traffic += (2*down_throughput)  # we consider the global p2p down traffic equal
									p2p_traffic.append(instant_p2p_traffic)     # to up traffic (multiplied by 2)
									yield self.env.timeout(transfer_time)
									# upload the list of downloaded files
									self.downloaded_files.append(file)
									self.individual_downtraffic.append(self.individual_downtraffic[-1] - down_throughput)
									peer.individual_uptraffic.append(peer.individual_uptraffic[-1] - down_throughput)
									instant_p2p_traffic -= (2*down_throughput)
									p2p_traffic.append(instant_p2p_traffic)
									server_flag = False
									# print "Device %r downloaded File %r from peer %r at %r" %(self.id, file.id, peer.id, self.env.now)
									break
								else:
									# time exceeded
									break

				if server_flag:
					# check if i have enough remaining time before log out
					if maxtime > self.env.now + transfer_time:
						instant_cloud_downtraffic += down_throughput
						cloud_downtraffic.append(instant_cloud_downtraffic)
						# download from the server
						yield self.env.timeout(transfer_time)
						# upload the list of downloaded files
						self.downloaded_files.append(file)
						#print "Device %r downloaded File %r from server at %r" % (self.id, file.id, self.env.now)
						instant_cloud_downtraffic -= down_throughput
						cloud_downtraffic.append(instant_cloud_downtraffic)


	def upload_proc(self, maxtime, folder):
		global instant_cloud_uptraffic
		global cloud_uptraffic

		file = get_random_file()
		up_throughput = get_throughput()
		# if up_throughput == 0:
			# print "up_throughput zero!", up_throughput
		transfer_time = file.get_size() / (8 * up_throughput)
		# check if the time is enough to complete the upload
		if maxtime > self.env.now + transfer_time:
			instant_cloud_uptraffic += up_throughput
			cloud_uptraffic.append(instant_cloud_uptraffic)
			yield self.env.timeout(transfer_time)
			instant_cloud_uptraffic -= up_throughput
			cloud_uptraffic.append(instant_cloud_uptraffic)

			# save the folders in which that file is contained
			file.my_folders.append(folder)
			# the file is contained in this device (owner)
			self.downloaded_files.append(file)
			# print "Device %r uploaded File %r at %r" % (self.id, file.id, self.env.now)

			# put the uploaded file into the download queue of other connected devices
			for device in folder.my_devices:
				if device.get_device_id() != self.id:
					device.download_queue.append(file)

	def session_off(self):
		# extract the duration of inter-session-time
		inter_session_time = random.lognormal(mean=7.971, sigma=1.308)
		# print (self.id,' device --> session off! @ ',self.env.now)
		yield self.env.timeout(inter_session_time)
		# print (self.id,' device has finish the session off! @ ',self.env.now)

	def session_on(self):
		# extract the duration of session
		session_time = random.lognormal(mean=8.492, sigma=1.545)
		# extract the maximum online time
		max_time = self.env.now + session_time
		# set the log out time for that device
		self.logout_time = max_time
		# extract randomly one connected folder
		folder = random.choice(self.my_shared_folders)

		while self.env.now < max_time:
			# start download process
			yield self.env.process(self.download_proc(max_time))
			# extract and wait the time among two uploads
			inter_upload_time = random.lognormal(mean=3.748, sigma=2.286)
			yield self.env.timeout(inter_upload_time)
			yield self.env.process(self.upload_proc(max_time, folder))

	def process(self):
		global devs
		global online_devs

		while True:
			devs += 1
			# print "devices now active are: ",devs
			online_devs.append(devs)
			yield self.env.process(self.session_on())

			devs -= 1
			# print "devices now active are: ",devs
			yield self.env.process(self.session_off())
			online_devs.append(devs)


# ******************************************************************************
# Create the synthetic content synchronization network
# ******************************************************************************
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


# ******************************************************************************
# SIMULATION
# ******************************************************************************
if __name__ == '__main__':

	# read the file THROUGHPUT.txt
	f = open("throughput.txt", "r")
	th_file = f.readlines()
	f.close()

	mean_active_devs = []
	mean_download_trf = []
	mean_upload_trf = []
	mean_cloud_download = []
	mean_cloud_upload = []
	mean_p2p_traffic = []
	mean_peer_downtraffic = []
	mean_peer_uptraffic = []


	for N in range(2, NUM_DEV):

		peer_downtraffic = []
		peer_uptraffic = []

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
		for peerID in devices:
			peer_downtraffic.append(numpy.mean(devices[peerID].individual_downtraffic))
			peer_uptraffic.append(numpy.mean(devices[peerID].individual_uptraffic))

		mean_active_devs.append(numpy.mean(online_devs))
		mean_cloud_download.append(numpy.mean(cloud_downtraffic))
		mean_cloud_upload.append(numpy.mean(cloud_uptraffic))
		mean_peer_downtraffic.append(numpy.mean(peer_downtraffic))
		mean_peer_uptraffic.append(numpy.mean(peer_uptraffic))
		mean_p2p_traffic.append(numpy.mean(p2p_traffic))

		# print "Mean # of active devices: ", numpy.mean(online_devs)
		# print "Mean server download traffic: ", numpy.mean(cloud_downtraffic)
		# print "Mean server upload traffic: ", numpy.mean(cloud_uptraffic)
		# print "Mean peer download traffic: ", numpy.mean(peer_downtraffic)
		# print "Mean peer upload traffic: ", numpy.mean(peer_uptraffic)
		# print "Mean global p2p traffic: ", numpy.mean(p2p_traffic)

		# fig, (active_devices, cloud_download_trf, cloud_upload_trf) = pyplot.subplots(3,1)
		#
		# active_devices.plot(online_devs)
		# active_devices.set_ylabel("Number of ACTIVE devices")
		#
		# cloud_download_trf.plot(cloud_downtraffic)
		# cloud_download_trf.set_ylabel("Download traffic")
		#
		# cloud_upload_trf.plot(cloud_uptraffic)
		# cloud_upload_trf.set_ylabel("Upload traffic")
		#
		#
		#
		# pyplot.figure(2)
		# pyplot.hist(online_devs, bins=100)
		# pyplot.figure(3)
		# pyplot.hist(cloud_uptraffic, bins=100)
		# pyplot.figure(4)
		# pyplot.hist(cloud_downtraffic, bins=100)
		# pyplot.show()

	print "mean_active_devs: ", mean_active_devs
	print "mean_cloud_download: ", mean_cloud_download
	print "mean_cloud_upload: ", mean_cloud_upload
	print "mean_p2p_traffic: ", mean_p2p_traffic
	print "mean_peer_downtraffic", mean_peer_downtraffic
	print "mean_peer_uptraffic", mean_peer_uptraffic

	fig, (active_devices, download_trf, upload_trf) = pyplot.subplots(3, 1)
	num = numpy.linspace(2, NUM_DEV, len(mean_active_devs))
	active_devices.plot(num, mean_active_devs)
	active_devices.set_xlabel("N - Number of devices")
	active_devices.set_ylabel("Mean # of ACTIVE devices")

	del num
	num = numpy.linspace(2, NUM_DEV, len(mean_cloud_download))
	download_trf.plot(num, mean_cloud_download)
	download_trf.set_xlabel("N - Number of devices")
	download_trf.set_ylabel("Mean Cloud Download traffic")

	del num
	num = numpy.linspace(2, NUM_DEV, len(mean_cloud_upload))
	upload_trf.plot(num, mean_cloud_upload)
	upload_trf.set_xlabel("N - Number of devices")
	upload_trf.set_ylabel("Mean Cloud Upload traffic")

	fig, (p2p_traffic, peer_downtraffic, peer_uptraffic) = pyplot.subplots(3, 1)
	num = numpy.linspace(2, NUM_DEV, len(mean_p2p_traffic))
	p2p_traffic.plot(num, mean_p2p_traffic)
	p2p_traffic.set_xlabel("N - Number of devices")
	p2p_traffic.set_ylabel("Mean p2p Global traffic")

	del num
	num = numpy.linspace(2, NUM_DEV, len(mean_peer_downtraffic))
	peer_downtraffic.plot(num, mean_peer_downtraffic)
	peer_downtraffic.set_xlabel("N - Number of devices")
	peer_downtraffic.set_ylabel("Mean peer Download traffic")

	del num
	num = numpy.linspace(2, NUM_DEV, len(mean_peer_uptraffic))
	peer_uptraffic.plot(num, mean_peer_uptraffic)
	peer_uptraffic.set_xlabel("N - Number of devices")
	peer_uptraffic.set_ylabel("Mean peer Upload traffic")
	pyplot.show()
