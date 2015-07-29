# -*- coding:GBK  -*-
'''
Created on 2013-6-23

@author: rena
'''

from common import common
import codecs
import os

class getMemberList(common.Tool):
        
    def __init__(self):
        # 获取配置文件
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
                    self.print_msg(str(e))
                    pass
        # 配置文件获取配置信息
        # 论坛相关
        self.fid = self.get_config(config, "FID", 1, 2)
        self.tid = self.get_config(config, "TID", 1, 2)
        self.endPageCount = self.get_config(config, "END_PAGE_COUNT", 1, 2)
        self.startPageCount = self.get_config(config, "START_PAGE_COUNT", 1, 2)
        self.isCorrectFlag = self.get_config(config, "CORRECT_FLAG", 1, 0)
        self.isIncorrectFlag = self.get_config(config, "INCORRECT_FLAG", 1, 0)
        # 操作系统&浏览器
        self.browerVersion = self.get_config(config, "BROWSER_VERSION", 2, 2)
        self.osVersion = self.get_config(config, "OS_VERSION", 1, 2)
        # cookie
        self.isAutoGetCookie = self.get_config(config, "IS_AUTO_GET_COOKIE", 1, 2)
        if self.isAutoGetCookie == 0:
            self.cookiePath = self.get_config(config, "COOKIE_PATH", "", 0)
        else:
            self.cookiePath = self.get_default_browser_cookie_path(self.osVersion, self.browerVersion)
        self.print_msg("配置文件读取完成")
        
    def main(self):
        # 设置系统cookies
        if not self.set_cookie(self.cookiePath, self.browerVersion):
            self.print_msg("导入浏览器cookies失败，程序结束！")
            self.process_exit()
        url = "http://club.snh48.com/forum.php?mod=viewthread&tid=%s&extra=&page=%s"  # 帖子地址
        self.ipUrl = "http://club.snh48.com/forum.php?mod=topicadmin&action=getip&fid=%s&tid=%s&pid=%s"  # ip查询地址
        floor = 1
        pageCount = self.startPageCount
        uidList = []
        ipList = []
        ipList2 = []
        resultFile = codecs.open(str(self.tid) + ".txt", 'w', 'GBK')
        resultFile.write("楼层\tuid\t用户名\t是否正确\tip\t是否实名\t其他备注\n")
        page = True
        while page:
            page = self.do_get(url % (self.tid, pageCount)).decode('utf-8')
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
                name = page[page.find('>', index + 55) + 1:page.find('</a>', index)]
                # 检查答案是否正确
                scoreIndex = page.find('<tbody class="ratl_l">', index, page.find('">点评</a>', index))
                score = ""
                if scoreIndex != -1:
                    scoreStart = page.find('<td class="xg1">', scoreIndex)
                    scoreStop = page.find('</tbody>', scoreIndex)
                    while scoreStart != -1:
                        score += page[scoreStart + 16:page.find('</td>', scoreStart)]
                        scoreStart = page.find('<td class="xg1">', scoreStart + 1, scoreStop)
                result = ""
                if score.find(self.isCorrectFlag) != -1:
                    result = "Y"
                elif  score.find(self.isIncorrectFlag) != -1:
                    result = "N"
                else:
                    result = score
        
                # 检查是否有二次编辑
                remarks = ""
                if page.find('<i class="pstatus">', index, page.find('<input type="checkbox" id="', index)) != -1:
                    remarks = "二次编辑"
                    result = "N"
                
                # 检查实名认证
                isReallyName = ""
                if page.find("实名认证", index, page.find('</div>', index)) == -1:
                    isReallyName = "未实名认证"
                    result = ""
                
                # ip
                if floor == 1:
                    ip = ""
                    ip2 = ""
                else:
                    pidStart = page.find('<div id="userinfo', index) 
                    pid = page[pidStart + len('<div id="userinfo'):page.find('_', pidStart)]
                    ipPage = self.do_get(self.ipUrl % (self.fid, self.tid, pid))
                    ip = ipPage[ipPage.find("<b>") + 3:ipPage.find("</b>")]
                    ip2 = ".".join(ip.split(".")[:2])
                # 检查是否二次回答
                if uid in uidList:
                    answerCount = uidList.count(uid)
                    lastFloor = 0
                    for i in range(answerCount):
                        lastFloor = uidList.index(uid, lastFloor + 1)
                    remarks += "多次回答，上一次回答楼层" + str(lastFloor + 1)                       
                uidList.append(uid)
                
                # 检查ip是否有重复
                if ip in ipList:
                    if remarks == "":
                        remarks += " ip与" + str(ipList.index(ip) + 1) + "楼相同"
                elif ip2 in ipList2:
                    remarks = " ip与" + str(ipList.index(ip) + 1) + "楼相似"
                ipList.append(ip)
                ipList2.append(ip)
                resultFile.write(floorName + "\t" + uid + "\t" + name + "\t" + result + "\t" + ip + "\t" + isReallyName + "\t" + remarks + "\n")
                index = page.find('<div class="authi"><a href="home.php?mod=space&amp;uid=', index + 1)
                floor += 1
            pageCount += 1
            # 帖子结束，退出
            if pageCount > self.endPageCount:
                break
                    
        self.print_msg("统计结束")
          
if __name__ == '__main__':
    getMemberList().main()
