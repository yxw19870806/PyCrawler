# -*- coding:GBK  -*-
'''
Created on 2015-2-5

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

# 自动在sql文件中追加表名并生产新的sql文件 

f = open('sql.txt', 'r')
line = f.readlines()
f.close()

ff = open('result.txt', 'w')
# GL s36 - s60
for i in range(36, 61):
    for l in line:
        l = l.replace('CREATE TABLE ', 'CREATE TABLE ' + 'gloryland' + str(i) + '.')
        ff.write(l)

ff.write('\n')

# HOG s0
for l in line:
    l = l.replace('CREATE TABLE ', 'CREATE TABLE ' + 'heroesofglory' + '.')
    ff.write(l)

ff.write('\n')

# GL s1 - s10           
for i in range(1, 11):
    for l in line:
        l = l.replace('CREATE TABLE ', 'CREATE TABLE ' + 'heroesofglory' + str(i) + '.')
        ff.write(l)

ff.close()