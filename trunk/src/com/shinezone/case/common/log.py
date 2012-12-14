import os, sys, inspect, time, traceback

def current_path():  
    path = os.path.realpath(sys.path[0])
    if os.path.isfile(path):
        path = os.path.dirname(path)
        return os.path.abspath(path)
    else:
        caller_file = inspect.stack()[1][1]
        return os.path.abspath(os.path.dirname(caller_file))

LOG_PATH = current_path() + "\\.." + "\\log\\"

def _date():
    return time.strftime('%Y-%m-%d', time.localtime(time.time()))

def _time():
    return time.strftime('%H:%M:%S', time.localtime(time.time()))

def write(string):
    path = LOG_PATH + "step_" + _date() + ".log"
    file = open(path, 'a')
    file.write(_time() + " " + string + "\n")
    file.close()

def writeErrorLog(string):
    path = LOG_PATH + "error_" + _date() + ".log"
    file = open(path, 'a')
    file.write(_time() + " " + string + "\n")
    file.close()

def writeExceptionLog():
    path = LOG_PATH + "error_" + _date() + ".log"
    file = open(path, 'a')
    file.write(_time() + "\n")
    traceback.print_exc(file=file)
    file.close()

def writeResultLog(string):
    path = LOG_PATH + "result_" + _date() + ".log"
    file = open(path, 'a')
    file.write(_time() + " " + string + "\n")
    file.close()

def writeBeforeStatus(status=[]):
    path = LOG_PATH + "status_" + _date() + ".log"
    file = open(path, 'a')
    string = ""
    for stat in status:
        string += str(stat.keys()[0]) + ": " + str(stat.values()[0]) + ", "
    string = "Before test:\t" + string
    file.write(_time() + " " + string + "\n")
    file.close()

def writeAfterStatus(status=[]):
    path = LOG_PATH + "status_" + _date() + ".log"
    file = open(path, 'a')
    string = ""
    for stat in status:
        string += str(stat.keys()[0]) + ": " + str(stat.values()[0]) + ", "
    string = "After test:\t" + string
    file.write(_time() + " " + string + "\n")
    file.close()

def writeCommunicateLog(request, response):
    path = LOG_PATH + "TEST_" + _date() + ".log"
    file = open(path, 'a')
    file.write(_time() + "\n\trequest: " + request + "\n\tresponse: " + response + "\n")
    file.close()

def writeSQLLog(SQL):
    path = LOG_PATH + "TEST_" + _date() + ".log"
    file = open(path, 'a')
    file.write(_time() + " SQL: " + SQL + "\n")
    file.close()

def writeDbResultLog(result):
    path = LOG_PATH + "TEST_" + _date() + ".log"
    file = open(path, 'a')
    file.write(_time() + " result: " + str(result) + "\n")
    file.close()
