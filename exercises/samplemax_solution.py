import random
import sys
from mpyc.seclists import seclist
from mpyc.runtime import mpc

"""
Run it with one party:
  python3 samplemax.py

Run it at once with 3 parties, of which 1 corrupted:
  python3 samplemax.py -M3 -T1

Run it in separate shells with 3 parties, of which 1 corrupted:
  python3 samplemax.py -M3 -T1 -I0
  python3 samplemax.py -M3 -T1 -I1
  python3 samplemax.py -M3 -T1 -I2
"""

secint = mpc.SecInt()
mpc.run(mpc.start())

n = len(mpc.parties)                  # number of parties
i = mpc.pid                           # my index
m = 10                                # input array length
B = 100*m                             # sum of inputs per party
k = max(n, B)                         # bound for encoding argmax


#
# fill inputs with random numbers that sum to B
#
inputs = [random.randrange(1, B) for j in range(0, m)]
isum = sum(inputs)                    # normalize inputs
for j in range(0, m):
    inputs[j] *= B/isum
    inputs[j] = int(inputs[j])
inputs[0] = B - sum(inputs[1:])       # adjust sum for possible rounding errors
print(f'Party {i} with inputs {inputs}, sum = {sum(inputs)}.')


#
# find maximal input element
#
slist = seclist([], secint)
smaxlist = seclist([], secint)
for j in range(0,m):
    for ii in range(0,n):
        slist.append(mpc.input(secint(inputs[j]), ii))
    smaxlist.append(mpc.max(slist))

maxmax = mpc.run(mpc.output(mpc.max(smaxlist)))
print(f'Maximal input element is {maxmax}.')


#
# find maximal input element and corresponding party
#
smax = secint(0)
sargmax = secint(0)
for j in range(0,m):
    for ii in range(0,n):
        v = mpc.input(secint(inputs[j]), ii)
        smaxtmp = mpc.if_else(v > smax, v, smax)
        sargmax = mpc.if_else(v > smax, secint(ii), sargmax)
        smax = smaxtmp

argmax = mpc.run(mpc.output(sargmax))
maxmax = mpc.run(mpc.output(smax))
print(f'Maximal input element is {maxmax}, from party {argmax}.')


mpc.run(mpc.shutdown())

