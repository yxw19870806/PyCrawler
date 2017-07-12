#! /usr/bin/env python
# -*- coding: UTF-8 -*-

'''
解数独
'''
#import sys,os

def scan(temp,i):
    heng=temp[(i/9*9):(i/9*9+9)]
    shu=[]
    for i0 in range(0,73,9):
        shu.append(temp[i%9+i0])
    kuai=[]
    row=i%9/3*3
    line=i/27*3
    for i0 in range(0,3):
        kuai.append(temp[line*9+row+i0])
        kuai.append(temp[(line+1)*9+row+i0])
        kuai.append(temp[(line+2)*9+row+i0])
    hsk=heng+shu+kuai
    hsk=list(set(hsk))
    data=[0,1,2,3,4,5,6,7,8,9]
    map(data.remove,hsk)
    return data

def myprint(temp):
    if not temp:
        print 'None'
    else:
        for i in range(0,73,9):
            print temp[i:i+9]

def easysolve(test):
    print 'try easy way...'
    changeflag=1
    while changeflag:
        changeflag=0
        for i in range(0,81):
            if not test[i]:
                numleft=scan(test,i)
                if not numleft:
                    return 0
                elif len(numleft)==1:
                    test[i]=numleft[0]
                    changeflag=1
    myprint(test)
    return test

def hardsolve(test):
    print 'try hard way...'
    i=0
    while i<81 and test[i]!=0:
        i=i+1
    if test[i]==0:
        numleft=scan(test,i)
        print i+1,':',numleft
        if not numleft:
            return 0
        elif len(numleft)==1:
            test[i]=numleft[0]
            temp=mysolve(test)
            if not temp:
                return 0
            else:
                test=temp
        else:
            for num in numleft:
                temp=test[:]
                temp[i]=num
                temp=mysolve(temp)
                if not temp:
                    continue
    return test
    

def mysolve(test):
    global result
    try:
        result;
    except:
        result=[]
    test=easysolve(test)
    if not test:
        print 'wrong'
        return 0
    elif min(test)!=0:
        result.append(test)
        return test
    else:
        test=hardsolve(test)
    return test

def shudu(test):
    global result
    result=[]
    mysolve(test)
    return result
    
result=[]
test=[\
0,9,0,0,6,7,0,1,4,\
0,6,2,0,1,0,0,9,0,\
1,5,7,3,0,9,0,2,6,\
0,4,8,1,0,0,7,0,0,\
0,1,9,0,7,8,6,0,0,\
0,0,5,0,2,4,1,8,0,\
9,0,0,4,0,1,0,7,5,\
0,7,0,0,5,0,0,6,0,\
5,2,0,0,8,6,0,3,0]
temp=shudu(test)
print 'Done\n'
if temp:
    i=1
    for one in temp:
        print 'result:',i
        i=i+1
        myprint(one)
