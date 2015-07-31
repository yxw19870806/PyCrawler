# -*- coding:UTF-8  -*-
'''
Created on 2013-8-28

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

import copy
import md5
import os
import random
import shutil
import time

from common import common, json

class Weibo(common.Tool):
    
    def _trace(self, msg):
        super(Weibo, self).trace(msg, self.isShowError, self.traceLogPath)
    
    def _print_error_msg(self, msg):
        super(Weibo, self).print_error_msg(msg, self.isShowError, self.errorLogPath)
        
    def _print_step_msg(self, msg):
        super(Weibo, self).print_step_msg(msg, self.isShowError, self.stepLogPath)
        
    def _visit(self, url):
        temp_page = self.do_get(url)
        if temp_page:
            redirect_url_index = temp_page.find("location.replace")
            if redirect_url_index != -1:
                redirect_url_start = temp_page.find("'", redirect_url_index) + 1
                redirect_url_stop = temp_page.find("'", redirect_url_start)
#                 redirectUrlStart = temp_page.find('"', redirect_url_index) + 1
#                 redirectUrlStop = temp_page.find('"', redirectUrlStart)
                redirect_url = temp_page[redirect_url_start:redirect_url_stop]
                return str(self.do_get(redirect_url))
            elif temp_page.find("用户名或密码错误") != -1:
                self._print_error_msg("登陆状态异常，请在浏览器中重新登陆微博账号")
                self.process_exit()
            else:
                try:
                    temp_page = temp_page.decode("utf-8")
                    if temp_page.find("用户名或密码错误") != -1:
                        self._print_error_msg("登陆状态异常，请在浏览器中重新登陆微博账号")
                        self.process_exit()
                except Exception, e:
                    pass
                return str(temp_page)
        return False

    def __init__(self):
        config = self.analyze_config(os.getcwd() + "\\..\\common\\config.ini")
        # 每次请求获取的图片数量
        self.IMAGE_COUNT_PER_PAGE = 20
        # 程序配置
        self.isLog = self.get_config(config, "IS_LOG", 1, 2)
        self.isShowError = self.get_config(config, "IS_SHOW_ERROR", 1, 2)
        self.isDebug = self.get_config(config, "IS_DEBUG", 1, 2)
        self.isShowStep = self.get_config(config, "IS_SHOW_STEP", 1, 2)
        self.isSort = self.get_config(config, "IS_SORT", 1, 2)
        self.getImageCount = self.get_config(config, "GET_IMAGE_COUNT", 0, 2)
        # 代理设置
        self.isProxy = self.get_config(config, "IS_PROXY", 2, 2)
        self.proxyIp = self.get_config(config, "PROXY_IP", "127.0.0.1", 0)
        self.proxyPort = self.get_config(config, "PROXY_PORT", "8087", 0)
        # 文件路径
        self.errorLogPath = self.get_config(config, "ERROR_LOG_FILE_NAME", "\\log\\errorLog.txt", 3)
        if self.isLog == 0:
            self.traceLogPath = ''
            self.stepLogPath = ''
        else:
            self.traceLogPath = self.get_config(config, "TRACE_LOG_FILE_NAME", "\\log\\traceLog.txt", 3)
            self.stepLogPath = self.get_config(config, "STEP_LOG_FILE_NAME", "\\log\\stepLog.txt", 3)
        self.imageDownloadPath = self.get_config(config, "IMAGE_DOWNLOAD_DIR_NAME", "\\photo", 3)
        self.imageTempPath = self.get_config(config, "IMAGE_TEMP_DIR_NAME", "\\tempImage", 3)
        self.userIdListFilePath = self.get_config(config, "USER_ID_LIST_FILE_NAME", "\\info\\idlist.txt", 3)
        # 操作系统&浏览器
        self.browserVersion = self.get_config(config, "BROWSER_VERSION", 2, 2)
        self.osVersion = self.get_config(config, "OS_VERSION", 1, 2)
        # cookie
        self.isAutoGetCookie = self.get_config(config, "IS_AUTO_GET_COOKIE", 1, 2)
        if self.isAutoGetCookie == 0:
            self.cookiePath = self.get_config(config, "COOKIE_PATH", "", 0)
        else:
            self.cookiePath = self.get_default_browser_cookie_path(self.osVersion, self.browserVersion)
        self.print_msg("配置文件读取完成")
            
    def main(self, user_id_list_file_path = '', image_download_path = '', image_temp_path = ''):
        if user_id_list_file_path != '':
            self.userIdListFilePath = user_id_list_file_path
        if image_download_path != '':
            self.imageDownloadPath = image_download_path
        if image_temp_path != '':
            self.imageTempPath = image_temp_path
        start_time = time.time()

        # 判断各种目录是否存在
        # 日志文件保存目录
        if self.isLog == 1:
            step_log_dir = os.path.dirname(self.stepLogPath)
            if not self.make_dir(step_log_dir, 0):
                self._print_error_msg("创建步骤日志目录：" + step_log_dir + " 失败，程序结束！")
                self.process_exit()
            trace_log_dir = os.path.dirname(self.traceLogPath)
            if not self.make_dir(trace_log_dir, 0):
                self._print_error_msg("创建调试日志目录：" + trace_log_dir + " 失败，程序结束！")
                self.process_exit()
        error_log_dir = os.path.dirname(self.errorLogPath)
        if not self.make_dir(error_log_dir, 0):
            self._print_error_msg("创建错误日志目录：" + error_log_dir + " 失败，程序结束！")
            self.process_exit()

        # 图片保存目录
        self._print_step_msg("创建图片根目录：" + self.imageDownloadPath)
        if not self.make_dir(self.imageDownloadPath, 2):
            self._print_error_msg("创建图片根目录：" + self.imageDownloadPath + " 失败，程序结束！")
            self.process_exit()

        # 设置代理
        if self.isProxy == 1:
            self.set_proxy(self.proxyIp, self.proxyPort, "http")
        # 设置系统cookies
        if not self.set_cookie(self.cookiePath, self.browserVersion):
            self._print_error_msg("导入浏览器cookies失败，程序结束！")
            self.process_exit()

        # 寻找idlist，如果没有结束进程
        user_id_list = {}
        if os.path.exists(self.userIdListFilePath):
            user_id_list_file = open(self.userIdListFilePath, 'r')
            all_user_list = user_id_list_file.readlines()
            user_id_list_file.close()
            for user_info in all_user_list:
                if len(user_info) < 5:
                    continue
                user_info = user_info.replace("\xef\xbb\xbf", "")
                user_info = user_info.replace(" ", "")
                user_info = user_info.replace("\n", "")
                user_info = user_info.replace("\r", "")
                user_info_list = user_info.split("\t")
                user_id_list[user_info_list[0]] = user_info_list
        else:
            self._print_error_msg("用户ID存档文件：" + self.userIdListFilePath + "不存在，程序结束！")
            self.process_exit()

        # 创建临时存档文件
        new_user_id_list_file_path = os.getcwd() + "\\info\\" + time.strftime('%Y-%m-%d_%H_%M_%S_', time.localtime(time.time())) + os.path.split(self.userIdListFilePath)[-1]
        new_user_id_list_file = open(new_user_id_list_file_path, 'w')
        new_user_id_list_file.close()
        # 复制处理存档文件
        new_user_id_list = copy.deepcopy(user_id_list)
        for newUserId in new_user_id_list:
            # 如果没有名字，则名字用uid代替
            if len(new_user_id_list[newUserId]) < 2:
                new_user_id_list[newUserId].append(new_user_id_list[newUserId][0])
            # 如果没有初始image count，则为0
            if len(new_user_id_list[newUserId]) < 3:
                new_user_id_list[newUserId].append("0")
            # 处理上一次image URL
            # 需置空存放本次第一张获取的image URL
            if len(new_user_id_list[newUserId]) < 4:
                new_user_id_list[newUserId].append("")
            else:
                new_user_id_list[newUserId][3] = ""
            # 处理成员队伍信息
            if len(new_user_id_list[newUserId]) < 5:
                new_user_id_list[newUserId].append("")

        allImageCount = 0
        for userId in sorted(user_id_list.keys()):
            user_name = new_user_id_list[userId][1]
            self._print_step_msg("UID: " + str(userId) + "，Name: " + user_name)
            # 初始化数据
            page_count = 1
            image_count = 1
            is_pass = False
            if len(user_id_list[userId]) <= 3 or user_id_list[userId][3] == '':
                is_error = False
            else:
                is_error = True

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if self.isSort == 1:
                image_path = self.imageTempPath
            else:
                image_path = self.imageDownloadPath + "\\" + user_name
            if not self.make_dir(image_path, 1):
                self._print_error_msg("创建图片下载目录：" + image_path + " 失败，程序结束！")
                self.process_exit()

            # 日志文件插入信息
            while 1:
                photo_album_url = "http://photo.weibo.com/photos/get_all?uid=%s&count=%s&page=%s&type=3" % (userId, self.IMAGE_COUNT_PER_PAGE, page_count)
                self._trace("相册专辑地址：" + photo_album_url)
                photo_page_data = self._visit(photo_album_url)
                self._trace("返回JSON数据：" + photo_page_data)
                try:
                    page = json.read(photo_page_data)
                except:
                    self._print_error_msg("返回信息不是一个JSON数据, user id: " + str(userId))
                    break

                # 总的图片数
                try:
                    total_image_count = page["data"]["total"]
                except:
                    self._print_error_msg("在JSON数据：" + str(page) + " 中没有找到'total'字段, user id: " + str(userId))
                    break

                try:
                    photo_list = page["data"]["photo_list"]
                except:
                    self._print_error_msg("在JSON数据：" + str(page) + " 中没有找到'total'字段, user id: " + str(userId))
                    break

                for image_info in photo_list:
                    if not isinstance(image_info, dict):
                        self._print_error_msg("JSON数据['photo_list']：" + str(image_info) + " 不是一个字典, user id: " + str(userId))
                        continue
                    if image_info.has_key("pic_name"):
                        # 将第一张image的URL保存到新id list中
                        if new_user_id_list[userId][3] == "":
                            new_user_id_list[userId][3] = image_info["pic_name"]
                        # 检查是否已下载到前一次的图片
                        if len(user_id_list[userId]) >= 4:
                            if image_info["pic_name"] == user_id_list[userId][3]:
                                is_pass = True
                                is_error = False
                                break
                        if image_info.has_key("pic_host"):
                            image_host = image_info["pic_host"]
                        else:
                            image_host = "http://ww%s.sinaimg.cn" % str(random.randint(1, 4))
                        try_count = 0
                        while True:
                            if try_count > 1:
                                image_host = "http://ww%s.sinaimg.cn" % str(random.randint(1, 4))
                            image_url = image_host + "/large/" + image_info["pic_name"]
                            if try_count == 0:
                                self._print_step_msg("开始下载第" + str(image_count) + "张图片：" + image_url)
                            else:
                                self._print_step_msg("重试下载第" + str(image_count) + "张图片：" + image_url)
                            imgByte = self.do_get(image_url)
                            if imgByte:
                                md5Digest = md5.new(imgByte).hexdigest()
                                # 处理获取的文件为weibo默认获取失败的图片
                                if md5Digest == 'd29352f3e0f276baaf97740d170467d7' or md5Digest == '7bd88df2b5be33e1a79ac91e7d0376b5':
                                    self._print_step_msg("源文件获取失败，重试")
                                else:
                                    file_type = image_url.split(".")[-1]
                                    if file_type.find('/') != -1:
                                        file_type = 'jpg'
                                    imageFile = open(image_path + "\\" + str("%04d" % image_count) + "." + file_type, "wb")
                                    imageFile.write(imgByte)
                                    self._print_step_msg("下载成功")
                                    imageFile.close()
                                    image_count += 1
                                break
                            else:
                                try_count += 1
                            if try_count >= 5:
                                self._print_error_msg("下载图片失败，用户ID：" + str(userId) + ", 第" + str(image_count) +  "张，图片地址：" + image_url)
                                break
                            
                    else:
                        self._print_error_msg("在JSON数据：" + str(image_info) + " 中没有找到'pic_name'字段, user id: " + str(userId))
                           
                    # 达到配置文件中的下载数量，结束
                    if len(user_id_list[userId]) >= 4 and user_id_list[userId][3] != '' and self.getImageCount > 0 and image_count > self.getImageCount:
                        is_pass = True
                        break
                if is_pass:
                    break
                if total_image_count / self.IMAGE_COUNT_PER_PAGE > page_count - 1:
                    page_count += 1
                else:
                    # 全部图片下载完毕
                    break
            
            self._print_step_msg(user_name + "下载完毕，总共获得" + str(image_count - 1) + "张图片")
            new_user_id_list[userId][2] = str(int(new_user_id_list[userId][2]) + image_count - 1)
            allImageCount += image_count - 1
            
            # 排序
            if self.isSort == 1:
                imageList = sorted(os.listdir(image_path), reverse=True)
                # 判断排序目标文件夹是否存在
                if len(imageList) >= 1:
                    destination_path = self.imageDownloadPath + "\\" + user_name
                    if not self.make_dir(destination_path, 1):
                        self._print_error_msg("创建图片子目录： " + destination_path + " 失败，程序结束！")
                        self.process_exit()

                    # 倒叙排列
                    if len(user_id_list[userId]) >= 3:
                        count = int(user_id_list[userId][2]) + 1
                    else:
                        count = 1
                    for fileName in imageList:
                        file_type = fileName.split(".")[1]
                        self.copy_files(image_path + "\\" + fileName, destination_path + "\\" + str("%04d" % count) + "." + file_type)
                        count += 1
                    self._print_step_msg("图片从下载目录移动到保存目录成功")
                # 删除临时文件夹
                shutil.rmtree(image_path, True)

            if is_error:
                self._print_error_msg(user_name + "图片数量异常，请手动检查")
                
            # 保存最后的信息
            new_user_id_list_file = open(new_user_id_list_file_path, 'a')
            new_user_id_list_file.write("\t".join(new_user_id_list[userId]) + "\n")
            new_user_id_list_file.close()

        stop_time = time.time()
        self._print_step_msg("存档文件中所有用户图片已成功下载，耗时" + str(int(stop_time - start_time)) + "秒，共计图片" + str(allImageCount) + "张")

if __name__ == '__main__':
    Weibo().main(os.getcwd() + "\\info\\idlist_1.txt", os.getcwd() +  "\\photo\\weibo1", os.getcwd() +  "\\photo\\weibo1\\tempImage")
    Weibo().main(os.getcwd() + "\\info\\idlist_2.txt", os.getcwd() +  "\\photo\\weibo2", os.getcwd() +  "\\photo\\weibo2\\tempImage")
    Weibo().main(os.getcwd() + "\\info\\idlist_3.txt", os.getcwd() +  "\\photo\\weibo3", os.getcwd() +  "\\photo\\weibo3\\tempImage")
    Weibo().main(os.getcwd() + "\\info\\idlist_4.txt", os.getcwd() +  "\\photo\\weibo4", os.getcwd() +  "\\photo\\weibo4\\tempImage")

