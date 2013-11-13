'''
Created on 2013-11-13

@author: rena
'''

old = ""
new = ""

count = len(old)
for i in range(count / 2):
    new += old[count - i * 2 - 1]
    
print new
