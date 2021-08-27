import random
from typing import List

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

def create_random_vector(n: int, b: int) -> List[int]:
    """create n random numbers that sum to b"""
    values = [random.randrange(1, b) for _ in range(n)]
    s = sum(values)  # normalize val
    values = [int(v * b / s) for v in values]
    values[0] = b - sum(values[1:])  # adjust sum for possible rounding errors
    return values


m = len(mpc.parties)                 # number of parties
n = 5                                # number of items
B = 100                              # sum of valuations per party
K = m ** n                           # number of allocations
val = create_random_vector(n=n, b=B)

mpc.run(mpc.start())
my_pid = mpc.pid                     # my index
secint = mpc.SecInt(16)              # working with 16-bit integers

print(f'Number of allocations = {K+1}.')
print(f'Party {my_pid} with valuations {val}, sum = {sum(val)}.')


#
# First version
#
print(f'\nComputing allocation, first version')

# find allocation that maximizes sum of valuations -- first version
max_worth = secint(0)
best_allocation = secint(0)
for allocation in range(K):
    s = secint(0)
    for i in range(n):
        # item i is allocated to P_j such that j is the i-th digit of `allocation` in base-m notation
        j = (allocation // m ** i) % m
        # print(f'{allocation} // {m**i} % {m} = {j} ')
        s += mpc.input(secint(val[i]), senders=j)  # total valuation of allocation

    best_allocation = mpc.if_else(s > max_worth, secint(allocation), best_allocation)
    max_worth = mpc.if_else(s > max_worth, s, max_worth)

best_allocation_public = mpc.run(mpc.output(best_allocation))
max_worth_public = mpc.run(mpc.output(max_worth))

print(f'Maximal allocation is worth {max_worth_public}, with allocation no. {best_allocation_public}:')
my_worth = 0
for i in range(n):
    j = (best_allocation_public // m ** i) % m
    print(f'Item {i} to P_{j}.')
    if j == my_pid:
        my_worth += val[i]
print(f'P_{my_pid} gets items worth {my_worth} and this is {"" if (my_worth > B / m) else "not "}'
      f'a proportional fair share.')


#
# Second version
#
print(f'\nComputing allocation, second version')

# each party shares its private valuation with the other parties in one step
V = mpc.input([secint(a) for a in val])

# anti cheater check
for i in range(m):
    sum = mpc.run(mpc.output(mpc.sum(V[i])))
    min = mpc.run(mpc.output(mpc.min(V[i])))
    max = mpc.run(mpc.output(mpc.max(V[i])))
    assert sum == B, f'Party {i} is cheating!'
    assert min >= 0, f'Party {i} is cheating!'
    assert max <= B, f'Party {i} is cheating!'

print('Input values of each party are sane')

# find the maximum over all allocations, using binary search from argmax()
am = mpc.argmax(mpc.sum(V[(a // m ** i) % m][i] for i in range(n)) for a in range(K))

argmax, maxsum = mpc.run(mpc.output(list(am)))
print(f'Maximal allocation is worth {maxsum}, with allocation no. {argmax}:')
worth = 0
for i in range(0, n):
    j = (argmax // m ** i) % m
    print(f'Item {i} to P_{j}.')
    if (j == my_pid):
        worth += val[i]
print(f'P_{my_pid} gets items worth {worth} and this is {"" if (worth > B / m) else "not "}a proportional '
      f'fair share.')

mpc.run(mpc.shutdown())

