# -*- coding:UTF-8  -*-
"""
命令行入口文件，非IDE执行
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import os
import sys


root_path = os.path.realpath(os.path.join(os.path.dirname(sys._getframe().f_code.co_filename), ".."))
if root_path not in sys.path:
    sys.path.append(root_path)
os.chdir(root_path)
