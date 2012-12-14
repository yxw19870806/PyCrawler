'''
Created on 2012-7-16

@author: Administrator
'''

class Message:
    def __init__ (self,aString):
        self.text = aString
    def printIt(self):
        print(self.text)


m1 = Message("Hello world")
m2 = Message("So long,it was short but sweet")
note = [m1,m2]
for msg in note:
    msg.printIt()