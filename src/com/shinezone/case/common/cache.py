import urllib2
import communication, config, log

def GetMemcache(key, value="", timeout=""):
    url = config.MEM_CACHE_URL % ("GET", key, value, timeout)
    request = urllib2.Request(url)
    response = urllib2.urlopen(request).read()
    if response.code != 200:
        log.write('memory cache get error, code:' + response.code)
        log.write("key: " + key)
        log.write("response: " + response)
        return False
    else:
        return communication.toJson(response)

def SetMemcache(key, value, timeout=60):
    if type(value) == list:
        value = str(value).replace("L", "")
    url = config.MEM_CACHE_URL % ("SET", key, value, timeout).replace("'", "\"")
    request = urllib2.Request(url);
    response = urllib2.urlopen(request).read();
    if response.code != 200:
        log.write('memory cache set error, code:' + response.code)
        log.write("key: " + key + ", value: " + str(value))
        log.write("response: " + response)
        return False
    else:
        return communication.toJson(response)
