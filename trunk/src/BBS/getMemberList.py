# -*- coding:utf-8  -*-
'''
Created on 2013-6-23

@author: rena
'''
import sys
import time
import traceback
import urllib2
import codecs

class getMemberList():
    
    def doGet(self, url):
        if url.find("http") == -1:
            return None
        count = 0
        while 1:
            try:
                request = urllib2.Request(url)
                if sys.version_info < (2, 7):
                    response = urllib2.urlopen(request)
                else:
                    response = urllib2.urlopen(request, timeout=20)
                return response.read()
            except Exception, e:
                self.printMsg(str(e))
                traceback.print_exc()
            count += 1
            if count > 10:
                self.printMsg("can not connection " + url)
                return False
    
    def main(self):
        tid = 14739
#         tid = 14273
        url = "http://club.snh48.com/forum.php?mod=viewthread&tid=%s&extra=&page=%s"
        
        resultFile = codecs.open("result", 'w', 'utf8')
        resultFile.write("楼层\tuid\t用户名\t是否实名\t其他备注\n")
        floor = 1
        pageCount = 1
        endPageCount = 8
        uidList = []
        page = self.doGet(url % (tid, pageCount)).decode('utf-8')
        while page:
            index = page.find('<div class="authi"><a href="home.php?mod=space&amp;uid=')
            while index != -1:
                # 楼层
                if floor == 1:
                    floorName = "楼主"
                elif floor == 2:
                    floorName = "沙发"
                elif floor == 3:
                    floorName = "板凳"
                elif floor == 4:
                    floorName = "地板"
                else:
                    floorName = str(floor)
                    
                # uid
                uid = page[index + 55:page.find('"', index + 55)]
                
                # 会员名
                name = page[page.find('>', index + 55) + 1:page.find('</a>', index)].encode('utf-8')
                
                # 检查实名认证
                isReallyName = ""
                if page.find("实名认证", index,page.find('</div>',index)) ==-1:
                    isReallyName= "未实名认证"               
                
                # 检查是否二次回答
                remarks = ""
                if uid in uidList:
                    remarks = "二次回答,第一次回答楼层" + str(uidList.index(uid) + 1)
                uidList.append(uid)

                try:
                    resultFile.write(floorName + "\t" + uid + "\t" + name + "\t" + isReallyName + "\t" + remarks + "\n")
                except:
                    print floorName, uid, name
                    resultFile.write(floorName + "\t" + uid + "\t" + "" + "\t" + "\n")
                index = page.find('<div class="authi"><a href="home.php?mod=space&amp;uid=', index + 1)
                floor += 1
            
            pageCount += 1
            if pageCount > endPageCount:
                break
            page = self.doGet(url % (tid, pageCount)).decode('utf-8')
        
if __name__ == '__main__':
    getMemberList().main()
