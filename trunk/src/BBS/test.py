'''
Created on 2013-7-15

@author: rena
'''
from BBS import sqlite2cookie
import cookielib
import os
import urllib2


#!/usr/bin/python


ckjar = sqlite2cookie.sqlite2cookie('C:\\Users\\rena\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\utt75g2c.default-1349100203494\\cookies.sqlite')


url = "http://club.akb48.com.cn/forum.php?mod=topicadmin&action=getip&fid=80&tid=23385&pid=11488716&ajaxmenu=1&inajax=1&ajaxtarget=_menu_content"
req = urllib2.Request(url)
req.add_header('User-Agent','Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(ckjar))
f = opener.open(req)
htm = f.read()
f.close()
print htm
# import requests
# s = requests.session()
# print s.get("http://club.akb48.com.cn/forum.php?mod=topicadmin&action=getip&fid=80&tid=23385&pid=11488716&ajaxmenu=1&inajax=1&ajaxtarget=_menu_content").text