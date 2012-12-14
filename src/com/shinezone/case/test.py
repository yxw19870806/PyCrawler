from common import communication, json
from com.shinezone.case.item import useEnergyProp
import urllib2, zlib, binascii
from com.shinezone.case.common import config, common
import random
#itemId =312321
#data = '["Guild","addGuild",[1,1,"tt","321"]]'
#data = '["Package","equipmerge",[%d]]' % (itemId)
#data = '["ShoppingMall","commonFlush",[]]'
#useEnergyProp.init(610022, 55)
#data =  '["Guild","getFriends",[]]'
#result = json.read(communication.request(data))
#print result 
#print result[1][1]
#print result[1][2]
#print result[1][3]
#print useEnergyProp.getStatus(610022)
def GetMemcache(key, value="", timeout=""):
    memcache_url = "http://dev-weibo-gloryland.shinezoneapp.com/dev_ycge/j7/j7.php?/test/Memcache/&type=%s&key=%s&value=%s&timeout=%s&token=218d681960530e8cba3bcc6af2236377&wyx_user_id=" + config.USER_ID
    url = memcache_url % ("GET", key, value, timeout)
    req = urllib2.Request(url)
    res = urllib2.urlopen(req).read()
    job = json.read(res)
    return job

def SetMemcache(key, value, timeout=60):
    memcache_url = "http://dev-weibo-gloryland.shinezoneapp.com/dev_ycge/j7/j7.php?/test/Memcache/&type=%s&key=%s&value=%s&timeout=%s&token=218d681960530e8cba3bcc6af2236377&wyx_user_id=" + config.USER_ID
    if str(type(value)) == "<type 'list'>":
        value = str(value).replace("L", "")        
    url = memcache_url % ("SET", key, value, timeout)
    url = url.replace("'", "\"")
    req = urllib2.Request(url);
    res = urllib2.urlopen(req).read();
    return res 


a =[1,2]
b= [3,4]

for i in a+b:
    print i
