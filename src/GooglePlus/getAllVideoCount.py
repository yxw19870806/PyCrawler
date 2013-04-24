'''
Created on 2013-4-17

@author: rena
'''

tempFile = open("allVideo.txt", 'r')
lines = tempFile.readlines()
tempFile.close()
count = 0
for line in lines:
    if line.find("plus.google.com") != -1:
        count += 1

print count
