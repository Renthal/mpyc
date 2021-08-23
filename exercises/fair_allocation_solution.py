import random
import sys
from mpyc.seclists import seclist
from mpyc.runtime import mpc

"""
Run it with one party:
  python3 fair_allocation.py

Run it at once with 3 parties, of which 1 corrupted:
  python3 fair_allocation.py -M3 -T1

Run it in separate shells with 3 parties, of which 1 corrupted:
  python3 fair_allocation.py -M3 -T1 -I0
  python3 fair_allocation.py -M3 -T1 -I1
  python3 fair_allocation.py -M3 -T1 -I2

"""


secint = mpc.SecInt(16)               # working with 16-bit integers
mpc.run(mpc.start())

n = len(mpc.parties)                  # number of parties
i = mpc.pid                           # my index
m = 8                                 # number of items
B = 100*m                             # sum of valuations per party
K = n**m                              # number of allocations


#
# fill input valuations with random numbers that sum to B
#
val = [random.randrange(1, B) for j in range(0, m)]
# for testing: val = [ 1 if (j%n) == i else 0 for j in range(0, m)]
isum = sum(val)                       # normalize val
for j in range(0, m):
    val[j] *= B/isum
    val[j] = int(val[j])
val[0] = B - sum(val[1:])             # adjust sum for possible rounding errors
print(f'Party {i} with valuations {val}, sum = {sum(val)}.')
print(f'Number of allocations = {K+1}.')

#
# First version
#
print(f'\nComputing allocation, first version')

# each party shares its private valuation with the other parties
V = mpc.input([secint(a) for a in val])

# find allocation that maximizes sum of valuations -- first version
smax = secint(0)
sargmax = secint(0)
for a in range(K):
    s = secint(0)
    for j in range(0,m):
        # item j is allocated to P_ii such that
        # ii is the j-th digit of allocation a in base-m notation
        ii = (a // n**j) % n
        s += mpc.input(secint(val[j]), ii)
    # total valuation of allocation is s
    smaxtmp = mpc.if_else(s > smax, s, smax)
    sargmax = mpc.if_else(s > smax, secint(a), sargmax)
    smax = smaxtmp

argmax = mpc.run(mpc.output(sargmax))
maxsum = mpc.run(mpc.output(smax))
print(f'Maximal allocation is worth {maxsum}, with allocation no. {argmax}:')
worth = 0
for j in range(0,m):
    ii = (argmax // n**j) % n
    print(f'Item {j} to P_{ii}.')
    if (ii == i):
        worth += val[j]

print(f'P_{i} gets items worth {worth} and this is {"" if (worth > B/n) else "not "}a proportional fair share.')

#
# Second version
#
print(f'\nComputing allocation, second version')

# each party shares its private valuation with the other parties in one step
V = mpc.input([secint(a) for a in val])

# find the maximum over all allocations, using binary search from argmax()
am = mpc.argmax(mpc.sum(V[(a // n**j) % n][j] for j in range(m)) for a in range(K))

argmax, maxsum = mpc.run(mpc.output(list(am)))
print(f'Maximal allocation is worth {maxsum}, with allocation no. {argmax}:')
worth = 0
for j in range(0,m):
    ii = (argmax // n**j) % n
    print(f'Item {j} to P_{ii}.')
    if (ii == i):
        worth += val[j]

print(f'P_{i} gets items worth {worth} and this is {"" if (worth > B/n) else "not "}a proportional fair share.')

mpc.run(mpc.shutdown())

