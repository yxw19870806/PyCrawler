'''
Created on 2013-11-13

@author: rena
'''
import random

randomList = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '_', '@']

old = "Not_P@55w0rd520"
new = ""

for i in old:
    new = str(random.choice(randomList)) + str(i) + new
    
print new
