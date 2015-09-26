from itertools import *
import math

items = (7,9,5,3,2)

for i in permutations(items, 5):
    value =int(i[0] + (i[1] * math.pow(i[2],2)) + math.pow(i[3],3) - i[4])
    values = i + (value,)
    #print("%s + %s * %s^2 + %s^3 - %s = %s" % values)
    if values[5] == 399:
        print(i)
