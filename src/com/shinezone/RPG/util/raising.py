class GetObjectTypeException(Exception):
    message = ""
    def __init__(self, msg):
        Exception.__init__(self)
        self.message = self.message + str(msg)
    def __str__(self):
        return self.message

class UnknownSystemException(Exception):
    message = ""
    def __init__(self, msg):
        Exception.__init__(self)
        self.message = self.message + str(msg)
    def __str__(self):
        return self.message
    
class ConfigNotInitException(Exception):
    message = "config file not init()"
    def __init__(self, msg=""):
        Exception.__init__(self)
        self.message = self.message + str(msg)
    def __str__(self):
        return self.message

#class SetAttrValueException(LoadAttrValueException):
#    def __init__(self, msg):
#        LoadAttrValueException.__init__(self, msg)
#    
#class GetAttrValueException(LoadAttrValueException):
#    def __init__(self, msg):
#        LoadAttrValueException.__init__(self, msg)
