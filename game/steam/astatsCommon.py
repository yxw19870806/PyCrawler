# -*- coding:UTF-8  -*-
"""
astats相关数据解析爬虫
http://astats.astats.nl/astats/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import output, net, robot, tool


# 获取指定游戏是否存在无效成就
def get_game_invalid_achievements(game_id):
    game_index_url = "http://astats.astats.nl/astats/Steam_Game_Info.php?AppID=%s" % game_id
    game_index_response = net.http_request(game_index_url)
    if game_index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        output.print_msg("游戏 %s 访问失败" % game_id)
        tool.process_exit()
    # game id 不存在
    if game_index_response.data.find("This game cannot be found in the database.") >= 0:
        return
    achievement_text = tool.find_sub_string(game_index_response.data, '<span class="GameInfoBoxRow">Achievements</span><br>', "</td>")
    # 没有成就
    if not achievement_text:
        return
    achievement_text = achievement_text.strip()
    if not robot.is_integer(achievement_text):
        invalid_achievement_text = tool.find_sub_string(achievement_text, '<font color="#FF0000">', "</font>")
        if invalid_achievement_text:
            output.print_msg("游戏 %s, 存在无效成就，%s" % (game_id, invalid_achievement_text))
        else:
            output.print_msg("游戏 %s, 存在未知成就文字：%s" % (game_id, invalid_achievement_text))
