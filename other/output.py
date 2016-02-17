__author__ = 'admin'

import os
import shutil


file_list = [
    '/common/config.ini',
    '/common/json.py',
    '/common/output.py',
    '/common/tool.py',
    '/common/config.ini',

    '/Blog/__init__.py',
    '/Blog/shinoda.py',

    '/bcy/__init__.py',
    '/bcy/Bcy.py',

    '/fkoji/__init__.py',
    '/fkoji/checkFkojiCount.py',
    '/fkoji/fkoji.py',

    '/googlePlus/__init__.py',
    '/googlePlus/checkCount.py',
    '/googlePlus/GooglePlus.py',

    '/instagram/__init__.py',
    '/instagram/checkInstagramCount.py',
    '/instagram/instagram.py',

    '/twitter/checkTwitterCount.py',
    '/twitter/twitter.py',

    '/weibo/weibo.py',
    '/weibo/checkWeiboCount.py'
]
save_data_list = [
    '/Blog/shinoda.save'
    '/bcy/info/idlist.txt',
    '/fkoji/fkoji.save',
    '/googlePlus/info/id.txt',
    '/googlePlus/info/idlist.txt',
    '/googlePlus/info/BK_idlist.txt',
    '/twitter/info/id.txt',
    '/twitter/info/idlist_1.txt',
    '/twitter/info/idlist_2.txt',
    '/twitter/info/idlist_3.txt',

    '/weibo/info/id.txt',
    '/weibo/info/idlist_1.txt',
    '/weibo/info/idlist_2.txt',
    '/weibo/info/idlist_3.txt',
    '/weibo/info/idlist_4.txt',
]
root_path = os.getcwd() + '/..'

dest_root_path = root_path + '/output/'

for file in file_list:
    sour_path = root_path + file
    dest_path = dest_root_path + file
    path = os.path.split(dest_path)[0]
    if not os.path.exists(path):
        os.makedirs(path)
    try:
        shutil.copyfile(sour_path, dest_path)
    except:
        print file + ' failed'
