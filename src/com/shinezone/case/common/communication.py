import urllib2, zlib
import config, json, log

def doPost(data, url=config.GAME_URL):
    request = urllib2.Request(url, data)
    response = urllib2.urlopen(request)
    file = response.read()
    if response.code != 200:
        log.write('communication error, code:' + response.code)
        log.write("request: " + data)
        return False
    else:
        return file

def encode(code):
    newCode = "aa" + code
    try:
        result = zlib.compress(newCode)
    except:
        log.write('encode error: ' + code)
        log.writeExceptionLog()
        return False
    return result

def decode(code):
    try:
        if code.find("Notice: ") != -1 or code.find("on line :") != -1 or code.find("ErrorInfo :") != -1:
            log.writeErrorLog(code)
        result = zlib.decompress(code)
    except:
        log.writeExceptionLog()
        return False
    return result

def request(data, isLog=True):
    code = encode(data)
    if code:
        response = doPost(code)
        if response:
            response = decode(response)
            if isLog:
                log.writeCommunicateLog(data, response)
            return response
        else:
            pass

def _changeType(li):
    if type(li) == list:
        for sub in range(len(li)):
            try:
                li[sub] = int(li[sub])
            except:
                pass
            if type(li[sub]) == list:
                _changeType(li[sub])
            elif type(li[sub]) == dict:
                _changeType(li[sub])
    elif type(li) == dict:
        for sub in li:
            if type(li[sub]) == list:
                _changeType(li[sub])
            elif type(li[sub]) == dict:
                _changeType(li[sub])
            elif sub[0] == "i":
                li[sub] = int(li[sub])
            elif sub[0] == "s":
                li[sub] = str(li[sub])
    return li

def toJson(string):
    js = json.read(string)
    return _changeType(js)
