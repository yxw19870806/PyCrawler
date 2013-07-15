# -*- coding:utf-8  -*-
'''
Created on 2013-6-23

@author: rena
'''
import Cookie
import codecs
import requests
import sys
import time
import traceback
import urllib2

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
                print e
                traceback.print_exc()
            count += 1
            if count > 10:
                self.printMsg("can not connection " + url)
                return False
    
    def main(self):
        # need
        tid = 15775
        endPageCount = 4
        
        fid = 61
        floor = 1
        pageCount = 1
        uidList = []
        ipList = []
        url = "http://club.snh48.com/forum.php?mod=viewthread&tid=%s&extra=&page=%s"
        ipUrl = "http://club.snh48.com/forum.php?mod=topicadmin&action=getip&fid=%s&tid=%s&pid=%s"  # % (fid, tid, pid)
        cookies = {}
        cookies["GkKI_2132_saltkey"] = "t9NwZ1Fc" 
        cookies["GkKI_2132_sid"] = "HGU220" 
        cookies["GkKI_2132_auth"] = "303cwGrBlpwGlNyC0Q5Eb1w9X0ONcGKtaL5c7%2B9Mh3vK4vbN99W2ZLzndojlQGgj7rlw3E6uIHdiA9Fi64kt4Dke" 
        #
#         cookies = Cookie.SimpleCookie()  
#         urllib2.build_opener(urllib2.HTTPCookieProcessor(ckjar) )
        
        resultFile = codecs.open(str(tid) + ".txt", 'w', 'utf8')
        resultFile.write("楼层\tuid\t用户名\tip\t是否实名\t其他备注\n")
        
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
                if page.find("实名认证", index, page.find('</div>', index)) == -1:
                    isReallyName = "未实名认证"               
                
                # ip
                if floor == 1:
                    ip = ""
                else:
                    pidStart = page.find('<div id="userinfo', index) 
                    pid = page[pidStart + len('<div id="userinfo'):page.find('_', pidStart)]
                    ipPage = requests.get(ipUrl % (fid, tid, pid), cookies=cookies).text
                    ip = ipPage[ipPage.find("<b>") + 3:ipPage.find("</b>")]
                
                # 检查是否二次回答
                remarks = ""
                if uid in uidList:
                    remarks = "二次回答,第一次回答楼层" + str(uidList.index(uid) + 1)
                uidList.append(uid)
                # 检查ip是否有重复
                if ip in ipList:
                    if remarks == "":
                        remarks = "ip与" + str(ipList.index(ip) + 1) + "楼相同"
                ipList.append(ip)
                    
                resultFile.write(floorName + "\t" + uid + "\t" + name + "\t" + ip + "\t" + isReallyName + "\t" + remarks + "\n")
                index = page.find('<div class="authi"><a href="home.php?mod=space&amp;uid=', index + 1)
                floor += 1
                
            pageCount += 1
            if pageCount > endPageCount:
                break
            page = self.doGet(url % (tid, pageCount)).decode('utf-8')
        
if __name__ == '__main__':
    getMemberList().main()
