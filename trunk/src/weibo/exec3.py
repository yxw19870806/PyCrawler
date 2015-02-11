# -*- coding:GBK  -*-
'''
Created on 2013-8-28

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

import os
from weibo import weibo

if __name__ == '__main__':
    weibo().main(os.getcwd() + "\\info\\idlist_3.txt", os.getcwd() +  "\\photo3", os.getcwd() +  "\\photo3\\tempImage")
