'''
Created on 2012-5-8

@author: ge
'''

import MySQLdb
import urllib2
import json

def select(sql,double=False):
    try:
        server='192.168.20.23';
        user ="root"
        database="test";
        passwd ="Lhi38rf3rd"
                
        conn=MySQLdb.connect(user=user,passwd=passwd,port=3306,db=database,host=server);
        
        cursor = conn.cursor()            
        
        cursor.execute(sql)
        job = cursor.fetchall()
        if str(job)=='()':
            return "null"
        if not double:
            job =job[0]
        conn.commit()
        conn.close()
        cursor.close()
        return job
    except:
        return -1

def update(sql):
    try:

        server='192.168.20.23';
        user ="root"
        database="test";
        passwd ="Lhi38rf3rd"
                
        conn=MySQLdb.connect(user=user,passwd=passwd,port=3306,db=database,host=server);
        
        cursor = conn.cursor()           
        
        line = cursor.execute(sql)
    #    job = cursor.fetchall()[0]
        conn.commit()
        conn.close()
        cursor.close()
        return line
    except:
        return -1

        
def GetMemcache(key,value="",timeout=""):
    memcache_url="http://dev-weibo-wm.shinezoneapp.com/dev_ycge/j7/j7.php?/test/Memcache/&type=%s&key=%s&value=%s&timeout=%s"
    url = memcache_url % ("GET",key,value,timeout)
    req=urllib2.Request(url)
    res=urllib2.urlopen(req).read()
    job=json.read(res)
    return job
    
def DelMemcache(key,value="",timeout=""):
    memcache_url="http://dev-weibo-wm.shinezoneapp.com/dev_ycge/j7/j7.php?/test/Memcache/&type=%s&key=%s&value=%s&timeout=%s"
    url = memcache_url % ("DEL",key,value,timeout)
    req=urllib2.Request(url);
    res=urllib2.urlopen(req).read();
    return res 

def SetMemcache(key,value,timeout=60):
    memcache_url="http://dev-weibo-wm.shinezoneapp.com/dev_ycge/j7/j7.php?/test/Memcache/&type=%s&key=%s&value=%s&timeout=%s"
    url = memcache_url % ("SET",key,value,timeout)
    req=urllib2.Request(url);
    res=urllib2.urlopen(req).read();
    return res   

#dict=json.read('{"aaa":{"aa":"bb","xx":"oo"},"bbb":{"aa":"bb","xx":"oo"}}')
#print dict['aaa']["aa"]
#FIGHT = 'FIGHT_%s';
#FRIENDS = 'USER_FRIENDS_%s'; 
#INTERACTION = 'USER_INTERACTION_%s';
#FRIENDWARTING = 'USER_FRIENDWARTING_%s';
#ACTIVE = 'USER_ACTIVE_%s';
#AVATAR = 'USER_AVATAR_%s';
#AVATAREXCHANGE = 'USER_AVATAREXCHANGE_%s';
#FRIENDINFO = 'USER_FRIENDINFO_%s';
#HEROEVENTFRIENDS = 'USER_HEROEVENTFRIENDS_%s';
#HEROEVENT = 'USER_HEROEVENT_%s_%s';
#VISTHEROEEVENT = 'USER_VISTHEROEEVENT_%s';
#http://dev-weibo-wm.shinezoneapp.com/dev_qa/j7/j7.php?/fsadmin/adminindex
#r_set("aa","bb","xx")
#print r_read("aa","bb")

#print SetMemcache("USER_VISTHEROEEVENT_1189917562",[234234,3434,22])