# -*- coding:UTF-8  -*-
"""
V聊app全推荐账号获取
http://www.vliaoapp.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
from project.vliao import vLiaoCommon

TAG_ID_LIST = [1, 2, 3, 4, 5, 9997, 9998]  # 好像 tag = 1就是全部账号


# 从API获取所有推荐账号
def get_account_list_from_api():
    account_list = {}
    for tag_id in TAG_ID_LIST:
        try:
            tag_account_list = get_tag_account_list(tag_id)
        except crawler.CrawlerException, e:
            output.print_msg("tag %s推荐账号解析失败，原因：%s" % (tag_id, e.message))
            raise
        output.print_msg("频道%s获取推荐账号%s个" % (tag_id, len(tag_account_list)))
        # 累加账号
        account_list.update(tag_account_list)
    return account_list


# 调用API获取tag内全部账号
def get_tag_account_list(tag_id):
    page_count = 1
    account_list = {}
    while True:
        output.print_msg("开始解析tag %s第%s页推荐账号" % (tag_id, page_count))
        account_pagination_url = "http://v3.vliao3.xyz/v%s/homepage" % vLiaoCommon.API_VERSION
        post_data = {
            "userId": vLiaoCommon.USER_ID,
            "userKey": vLiaoCommon.USER_KEY,
            "tagId": tag_id,
            "page": page_count,
        }
        account_pagination_response = net.http_request(account_pagination_url, method="POST", fields=post_data, json_decode=True)
        if account_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
            raise crawler.CrawlerException(crawler.request_failre(account_pagination_response.status))
        # 获取全部账号id
        if not crawler.check_sub_key(("data",), account_pagination_response.json_data):
            raise crawler.CrawlerException("返回信息'data'字段不存在\n%s" % account_pagination_response.json_data)
        for account_info in account_pagination_response.json_data["data"]:
            # 获取账号id
            if not crawler.check_sub_key(("id",), account_info):
                raise crawler.CrawlerException("账号信息'id'字段不存在\n%s" % account_info)
            if not crawler.is_integer(account_info["id"]):
                raise crawler.CrawlerException("账号信息'id'字段类型不正确\n%s" % account_info)
            account_id = str(account_info["id"])
            # 获取账号昵称
            if not crawler.check_sub_key(("nickname",), account_info):
                raise crawler.CrawlerException("账号信息'title'字段不存在\n%s" % account_info)
            account_name = str(account_info["nickname"].encode("UTF-8"))
            account_list[account_id] = account_name

        # 判断是不是最后一页
        if not crawler.check_sub_key(("maxPage",), account_pagination_response.json_data):
            raise crawler.CrawlerException("返回信息'maxPage'字段不存在\n%s" % account_pagination_response.json_data)
        if not crawler.is_integer(account_pagination_response.json_data["maxPage"]):
            raise crawler.CrawlerException("返回信息'maxPage'字段类型不正确\n%s" % account_pagination_response.json_data)
        if page_count >= int(account_pagination_response.json_data["maxPage"]):
            break
        else:
            page_count += 1
    return account_list


def main():
    # 检测登录状态
    if not vLiaoCommon.check_login():
        log.error("没有检测到登录状态，退出程序")
        tool.process_exit()

    account_list_from_api = get_account_list_from_api()

    if len(account_list_from_api) > 0:
        # 存档位置
        save_data_path = crawler.quickly_get_save_data_path()
        account_list_from_save_data = crawler.read_save_data(save_data_path, 0, [])
        for account_id in account_list_from_api:
            if account_id not in account_list_from_save_data:
                account_list_from_save_data[account_id] = [account_id, "", account_list_from_api[account_id]]
        temp_list = [account_list_from_save_data[key] for key in sorted(account_list_from_save_data.keys())]
        tool.write_file(tool.list_to_string(temp_list), save_data_path, tool.WRITE_FILE_TYPE_REPLACE)


if __name__ == "__main__":
    main()
