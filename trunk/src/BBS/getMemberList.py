# -*- coding:utf-8  -*-
'''
Created on 2013-6-23

@author: rena
'''
from common import common
import codecs
import os

class getMemberList():
    
    def main(self):
        # 获取配置信息
        processPath = os.getcwd()
        configFile = open(processPath + "\\config.ini", 'r')
        lines = configFile.readlines()
        configFile.close()
        config = {}
        for line in lines:
            line = line.lstrip().rstrip().replace(" ", "")
            if len(line) > 1 and line[0] != "#":
                try:
                    line = line.split("=")
                    config[line[0]] = line[1]
                except Exception, e:
                    self.printMsg(str(e))
                    pass
        # 帖子id
        tid = common.getConfig(config, "TID", 1, 2)
        # 帖子页数
        endPageCount = common.getConfig(config, "PAGE_COUNT", 1, 2)
        # 版块id
        fid = 61
        # 帖子地址
        url = "http://club.snh48.com/forum.php?mod=viewthread&tid=%s&extra=&page=%s"
        # ip查询地址
        ipUrl = "http://club.snh48.com/forum.php?mod=topicadmin&action=getip&fid=%s&tid=%s&pid=%s"  # % (fid, tid, pid)
        # 其他初始化数据
        floor = 1
        pageCount = 1
        uidList = []
        ipList = []

        # 设置系统cookies (fire fox)
        common.cookie("C:\\Users\\Administrator\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\xozaopr2.default\\cookies.sqlite")
        
        resultFile = codecs.open(str(tid) + ".txt", 'w', 'utf8')
        resultFile.write("楼层\tuid\t用户名\tip\t是否实名\t其他备注\n")
        page = common.doGet(url % (tid, pageCount)).decode('utf-8')
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
                    ipPage = common.doGet(ipUrl % (fid, tid, pid)).decode('utf-8')
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
            # 帖子结束，退出
            if pageCount > endPageCount:
                break
            page = common.doGet(url % (tid, pageCount)).decode('utf-8')
        
if __name__ == '__main__':
    getMemberList().main()
