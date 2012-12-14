'''
Created on 2012-5-23

@author: Administrator
'''
#alist=[1, 2.0, 'a', "b", '3', True]
#aTuple=(1, 2.0, 'a', "b", '3', True)
#print alist[2:4]
#try:
#    filename = raw_input('Enter file name: ')
#    fobj = open(filename, 'r')
#    for eachLine in fobj:
#        print eachLine
#    fobj.close()
#except IOError, e:
#    print 'f1.xtile open error:', e

try:
    filename = raw_input('Enter file name: ')
    fobj = open(filename, 'r')
    for eachLine in fobj:
        print eachLine, fobj.close()
except IOError, e:
    print 'file open error:', e