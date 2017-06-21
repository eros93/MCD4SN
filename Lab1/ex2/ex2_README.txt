
LAB 1 [EX2] - Varying the hit probability

Granularity = 50	(different values of arrival time in each simulation)

# batches in each simulation = 20

Dim group (batch arrival) of packets: unif distr [1,5]

Buffer FrontEnd = 10000
Buffer BackEnd = 10000

Confidence interval = 0.9

Warm Up Removal: first batch is removed

Seed = 7	(equal for all simulations)


#######
# Using the figure of the lab sheets P is the probability that a reqs not satisfied by Front End
# HIT PROBABILITY OF FRONT END = 1-P
######

P = [0.25 0.375 0.5 0.625 0.75]