# -*- coding:UTF-8  -*-
"""
微博批量关注账号
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import time
from common import *
from . import weiboCommon

COOKIE_INFO = {"SUB": ""}


# 关注指定账号
def follow_account(account_id):
    api_url = "http://weibo.com/aj/f/followed?ajwvr=6"
    post_data = {
        "uid": account_id,
        "refer_flag": "1005050001_",
    }
    header_list = {"Referer": "http://weibo.com/%s/follow" % account_id}
    cookies_list = {"SUB": COOKIE_INFO["SUB"]}
    follow_response = net.http_request(api_url, method="POST", fields=post_data, header_list=header_list, cookies_list=cookies_list, json_decode=True)
    if follow_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        output.print_msg("关注%s失败，请求返回结果：%s" % (account_id, crawler.request_failre(follow_response.status)))
        tool.process_exit()
    if not (crawler.check_sub_key(("code",), follow_response.json_data) and crawler.is_integer(follow_response.json_data["code"])):
        output.print_msg("关注%s失败，请求返回结果：%s" % (account_id, crawler.request_failre(follow_response.status)))
        tool.process_exit()
    if int(follow_response.json_data["code"]) == 100000:
        output.print_msg("关注%s成功" % account_id)
        time.sleep(5)
        return True
    elif int(follow_response.json_data["code"]) == 100027:
        output.print_msg("关注%s失败，连续关注太多用户需要输入验证码，等待一会儿继续尝试" % account_id)
        # sleep 一段时间后再试
        time.sleep(60)
    elif int(follow_response.json_data["code"]) == 100001:
        output.print_msg("达到今日关注上限，退出程序" % account_id)
        tool.process_exit()
    else:
        output.print_msg("关注%s失败，返回内容：%s，退出程序！" % (account_id, follow_response.json_data))
        tool.process_exit()
    return False


def main():
    config = crawler._get_config()

    # 获取cookies
    all_cookie_from_browser = crawler.quickly_get_all_cookies_from_browser(config)
    if ".sina.com.cn" in all_cookie_from_browser:
        for cookie_key in all_cookie_from_browser[".sina.com.cn"]:
            COOKIE_INFO[cookie_key] = all_cookie_from_browser[".sina.com.cn"][cookie_key]
    else:
        output.print_msg("没有检测到登录信息")
        tool.process_exit()
    if ".login.sina.com.cn" in all_cookie_from_browser:
        for cookie_key in all_cookie_from_browser[".login.sina.com.cn"]:
            COOKIE_INFO[cookie_key] = all_cookie_from_browser[".login.sina.com.cn"][cookie_key]
    else:
        output.print_msg("没有检测到登录信息")
        tool.process_exit()

    # 检测登录状态
    if not weiboCommon.check_login(COOKIE_INFO):
        # 如果没有获得登录相关的cookie，则模拟登录并更新cookie
        new_cookies_list = weiboCommon.generate_login_cookie(COOKIE_INFO)
        if new_cookies_list:
            COOKIE_INFO.update(new_cookies_list)
        # 再次检测登录状态
        if not weiboCommon.check_login(COOKIE_INFO):
            output.print_msg("没有检测到您的登录信息，无法关注账号，退出！")
            tool.process_exit()

    # 存档位置
    save_data_path = crawler.quickly_get_save_data_path(config)
    # 读取存档文件
    account_list = crawler.read_save_data(save_data_path, 0, [])
    for account_id in sorted(account_list.keys()):
        while not follow_account(account_id):
            pass

    output.print_msg("关注完成")

if __name__ == "__main__":
    main()
