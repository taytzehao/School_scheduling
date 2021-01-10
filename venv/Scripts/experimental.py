import random
import numpy as np
from itertools import groupby
import time
from deap import tools
from collections import deque
from copy import deepcopy
##from collections import set
'''
class example():
    instance=[]

    def __init__(self,b):
        self.value=b
        self.__class__.instance.append(self)


eg_a=example(6)
eg_b=example(7)
copied=deepcopy(example.instance)
dict_eg=dict([i.value,i] for i in copied)
try:
    dict_eg[7]
except :
    print("lala")


print(dict_eg)

'''
a=list(range(100000))

t0=time.perf_counter()
a.append(7)
a.pop()
t1=time.perf_counter()
print(t1-t0)

a=deque(list(range(100000)))

t0=time.perf_counter()
a.append(7)
a.pop()
t1=time.perf_counter()
print(t1-t0)


