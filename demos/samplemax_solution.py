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

# Create a SecInt() placeholder with no value yet
# This is in Essence a class that inherits from SecureInteger. secint instantiation accepts a value -> secint(value)
# The value is mapped onto a Galois Field, defined in secint.field
secint = mpc.SecInt()
# Connect all parties with each other
mpc.run(mpc.start())

n = len(mpc.parties)                  # number of parties
i = mpc.pid                           # my index
m = 10                                # input array length
B = 100*m                             # sum of inputs per party
k = max(n, B)                         # bound for encoding argmax


#
# fill inputs with random numbers that sum to B
# B/isum clculates the factor by which the input needs to be changed such that inputs sum to B
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

#A secure list contains secret-shared numbers. Apart from hiding the contents of the
#list, however, it is also possible to hide which items are accessed and which items
#are updated. In principle, only the length of a secure list remains public.
# Subclasses list type so functionality is almost the same for non secure types as with normal list
slist = seclist([], secint)
smaxlist = seclist([], secint)
for j in range(0,m):
    # j Go through all 10 values in list
    for ii in range(0,n):
        # ii Go through all parties
        # secint creates a SecInt Object which contains a field entity which handles GF 
        # - l = runtime.options.bit_length (32)
        # - n = 2
        # - f = 0
        # SecInt.fields = Results in finfields.GF((9223372036854775907, 2, 9223372036854775906), 0)
        
        # SecInt:
        #  name = f'SecInt{l}' if p is None else f'SecInt{l}({p})'                                                                                                                                                        
        #  sectype = type(name, (SecureInteger,), {'__slots__': ()})                                                                                                                                                      
        #  sectype.__doc__ = 'Class of secret-shared integers.'                                                                                                                                                           
        #  sectype.field = _pfield(l, 0, p, n)                                                                                                                                                                            
        #  sectype.bit_length = l                                                                                                                                                                                         
        #  globals()[name] = sectype  # NB: exploit (almost) unique name dynamic SecureInteger type                                                                                                                       
        #  return sectype  
       
        # Note
        # sectype = type(name, (SecureInteger,), {'__slots__': ()})
        # sectype is a class object deriving from SecureInteger which takes a value in its __init__, this is where inputs[j] goes
        
        # value = self.field(value) it uses the GF Field above which is a finfields.GF and maps that value to the field
        
        ## INPUT
        # input calls _distribute, x is secint, sender ii is int 
        # self._distribute([SecInt32:SecureInteger(value[j])], [sender])

        
        # when the output of mpc.input is not of securetype securelist will first create one with self.sectype(value) before appending

        """
        mpc.input:
        Input x to the computation.
        Value x is a secure object, or a list of secure objects.
        The senders are the parties that provide an input.
        The default is to let every party be a sender.
        """

        #Build execution graph for  jth input and all parties, append them to secure list
        # Input: Create shares that are sent (senders!) to each other
        #in_shares = thresha.random_split(x, t, m), take secure value x, t is the thershold (probably degree of polynomial, m is number of senders
        slist.append(mpc.input(secint(inputs[j]), ii))

    # maximum value over s list which contains secure jth elements over all parties 
    smaxlist.append(mpc.max(slist))

# Global maximum

# Compute maximum over maxima of jth value for all parties m values per party, so we should have m x n(parties) values, so we have m values in the smaxlist
# max max is max([list with m values]), thus the global maximum value

#mpc.output is responsible for gathering all shares and recombining them to the correct output, this can be computed by all receivers
# mpc run starts execution of all coroutines that are inside the loop, until all futures recevied actual values
maxmax = mpc.run(mpc.output(mpc.max(smaxlist)))
print(f'Maximal input element is {maxmax}.')


#
# find maximal input element and corresponding party
#
# This finds the index of the maximum value for each of the lists given by a party
smax = secint(0)
sargmax = secint(0)
for j in range(0,m): #Nr of values per list of each party
    for ii in range(0,n): #Nr of parties, go through each party
        v = mpc.input(secint(inputs[j]), ii)
        smaxtmp = mpc.if_else(v > smax, v, smax)
        sargmax = mpc.if_else(v > smax, secint(ii), sargmax)
        smax = smaxtmp

argmax = mpc.run(mpc.output(sargmax))
maxmax = mpc.run(mpc.output(smax))
print(f'Maximal input element is {maxmax}, from party {argmax}.')


mpc.run(mpc.shutdown())

