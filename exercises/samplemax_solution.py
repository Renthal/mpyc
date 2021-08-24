import random
import sys
from mpyc.seclists import seclist
from mpyc.runtime import mpc
import sys

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

m = len(mpc.parties)                  # number of parties
i = mpc.pid                           # my index
n = 10                                # input array length
B = 100*n                             # sum of inputs per party
k = max(m, B)                         # bound for encoding argmax


#
# fill inputs with random numbers that sum to B
#
inputs = [random.randrange(1, B) for val_idx in range(0, n)]
isum = sum(inputs)                    # normalize inputs
for val_idx in range(0, n):
    inputs[val_idx] *= B/isum
    inputs[val_idx] = int(inputs[val_idx])
inputs[0] = B - sum(inputs[1:])       # adjust sum for possible rounding errors
print(f'Party {i} with inputs {inputs}, sum = {sum(inputs)}.')

#
# find maximal input element
#
#slist = seclist([], secint)
print("Version 1 ------------------------")
smaxlist = seclist([], secint)
for val_idx in range(0,n):
    slist = seclist([], secint)
    for party_idx in range(0,m):
        slist.append(mpc.input(secint(inputs[val_idx]), party_idx))
    smaxlist.append(mpc.max(slist))

maxmax = mpc.run(mpc.output(mpc.max(smaxlist)))
print(f'Version 1: Maximal input element is {maxmax}.')

print("Version 2 ------------------------")
smaxlist = seclist([], secint)
max_value = max(inputs)
print(f"My max input {i}: {max_value}")

for party_idx in range(0,m):
    smaxlist.append(mpc.input(secint(max_value), party_idx))

maxmax = mpc.run(mpc.output(mpc.max(smaxlist)))
print(f'Version 2: Maximal input element is {maxmax}.')


print("Version 3 ------------------------")
#
# find maximal input element and corresponding party
#
smax = secint(0)
sargmax = secint(0)
for val_idx in range(0,n):
    for party_idx in range(0,m):
        v = mpc.input(secint(inputs[val_idx]), party_idx)
        smaxtmp = mpc.if_else(v > smax, v, smax)
        sargmax = mpc.if_else(v > smax, secint(party_idx), sargmax)
        smax = smaxtmp

argmax = mpc.run(mpc.output(sargmax))
maxmax = mpc.run(mpc.output(smax))
print(f'Maximal input element is {maxmax}, from party {argmax}.')



print("Version 4 ------------------------")
#
# find maximal input element and corresponding party
#
smax = secint(0)
sargmax = secint(0)
for val_idx in range(0,n):
    for party_idx in range(0,m):
        v = mpc.input(secint(inputs[val_idx]), party_idx)
        sargmax = mpc.if_else(v > smax, secint(party_idx), sargmax)
        smax = mpc.if_else(v > smax, v, smax)

argmax = mpc.run(mpc.output(sargmax))
maxmax = mpc.run(mpc.output(smax))
print(f'Maximal input element is {maxmax}, from party {argmax}.')

mpc.run(mpc.shutdown())

