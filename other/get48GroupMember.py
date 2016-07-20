# -*- coding:UTF-8  -*-
"""
fkoji图片爬虫
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import tool
import re


def akb():
    members_list = []
    for team_id in [1, 2, 3, 4, 12, 15]:
        index_url = "http://www.akb48.co.jp/about/members/?team_id=" + str(team_id)
        return_code, page = tool.http_request(index_url)[:2]
        if return_code == 1:
            member_list_find = re.findall('<ul class="memberListUl">([\s|\S]*?)</ul>', page)
            if len(member_list_find) == 1:
                member_list = re.findall("<li>([\s|\S]*?)</li>", member_list_find[0])
                for member in member_list:
                    member = member.replace("<br />", "").replace("\n", "").replace("\r", "").replace("\t", "")
                    japanese_name_find = re.findall('<h4 class="memberListNamej">([^<]*)</h4>', member)
                    english_name_find = re.findall('<p class="memberListNamee">([^<]*)</p>', member)
                    team_find = re.findall('<h5 class="memberListTeam">([^<]*)</h5>', member)
                    if len(japanese_name_find) != 1:
                        print "error japanese_name_find"
                        continue
                    if len(english_name_find) != 1:
                        print "error english_name_find"
                        continue
                    if (team_id != 12 and len(team_find) != 1) or (team_id == 12 and len(team_find) != 2):
                        print "error team_find"
                        continue

                    japanese_name = japanese_name_find[0].replace(" ", "")
                    first_name, last_name = english_name_find[0].split(" ", 1)
                    team = team_find[0].strip().replace("  /", " / ")
                    members_list.append([japanese_name, last_name + " " + first_name, team])
            else:
                print "error member_list_find"
    return members_list


def ske():
    split_list = {
        "SKE48 Team S": ("<!-- LIST - TEAM S -->", "<!-- //LIST - TEAM S -->"),
        "SKE48 Team KII": ("<!-- LIST - TEAM KII -->", "<!-- //LIST - TEAM KII -->"),
        "SKE48 Team E": ("<!-- LIST - TEAM E -->", "<!-- //LIST - TEAM E -->"),
        "SKE48 Team Kenkyusei": ("<!-- LIST - KENKYUSEI -->", "<!-- //LIST - KENKYUSEI -->")
    }
    members_list = []
    index_url = "http://www.ske48.co.jp/profile/list.php"
    return_code, page = tool.http_request(index_url)[:2]
    if return_code == 1:
        for team_name in split_list:
            team_page = page[page.find(split_list[team_name][0]):page.find(split_list[team_name][1])]
            member_list = re.findall('<dl>([\s|\S]*?)</dl>', team_page)
            for member in member_list:
                member = member.replace("<br />", "").replace("\n", "").replace("\r", "").replace("\t", "")
                japanese_name_find = re.findall('<h3><a href="./\?id=[^"]*">([^<]*)</a></h3>', member)
                english_name_find = re.findall('<h3 class="en">([^<]*)</h3>', member)
                plus_text_find = re.findall('<li class="textPlus">([\s|\S]*?)</li>', member)
                if len(japanese_name_find) != 1:
                    print "error japanese_name_find"
                    continue
                if len(english_name_find) != 1:
                    print "error english_name_find"
                    continue
                if len(plus_text_find) != 1:
                    print "error plus_text_find"
                    continue

                japanese_name = japanese_name_find[0].replace(" ", "")
                first_name, last_name = english_name_find[0].strip().title().split(" ", 1)
                if plus_text_find[0].find("兼任") > 0:
                    team = team_name + " / " + plus_text_find[0].split("/")[-1].strip().replace("チーム", " Team ").replace("兼任", "")
                else:
                    team = team_name
                members_list.append([japanese_name, last_name + " " + first_name, team])
    return members_list


def nmb():
    team_list = {
        "teamn": "NMB48 Team N",
        "teamm": "NMB48 Team M",
        "teamb2": "NMB48 Team BII",
        "dkenkyusei": "NMB48 Team Kenkyusei",
        "kenkyusei": "NMB48 Team Kenkyusei",
    }
    members_list = []
    index_url = "http://www.nmb48.com/member/"
    return_code, page = tool.http_request(index_url)[:2]
    if return_code == 1:
        team_page_list = re.findall('<!--▼チーム別領域ボックス▼-->([\s|\S]*?)<!--▲チーム別領域ボックス▲--> ', page)
        for team_page in team_page_list:
            team_find = re.findall('<a name="([^"]*)"></a>', team_page)
            if len(team_find) == 1:
                if team_find[0] not in team_list:
                    print "not found " + team_find[0] + " in team_list"
                    continue
                member_list = re.findall('<li class="member-box[^"]*">([\s|\S]*?)</li>', team_page)
                for member in member_list:
                    member = member.replace("<br />", "").replace("\n", "").replace("\r", "").replace("\t", "").replace("&nbsp;", " ")
                    japanese_name_find = re.findall('<h4><a href="[^"]*">([^<]*)</a></h4>', member)
                    english_name_find = re.findall('<p[\s|\S]*?>([\s|\S]*?)</[p|a]>', member)
                    if len(japanese_name_find) != 1:
                        print "error japanese_name_find"
                        continue
                    if len(english_name_find) != 1:
                        print "error english_name_find"
                        continue

                    team = team_list[team_find[0]]
                    if english_name_find[0].find("<span>") >= 0:
                        temp = english_name_find[0].split("<span>")
                        english_name_find[0] = temp[0]
                        temp[1] = temp[1].replace("</span>", "")
                        if temp[1].find("研究生") == -1:
                            team += " / " + temp[1].split("/")[-1].strip()
                    japanese_name = japanese_name_find[0].replace("　", " ").replace(" ", "")
                    first_name, last_name = english_name_find[0].strip().title().split(" ", 1)
                    members_list.append([japanese_name, last_name + " " + first_name, team])
            else:
                print "error team_find"
    return members_list


def hkt():
    members_list = []
    index_url = "http://www.hkt48.jp/profile/"
    return_code, page = tool.http_request(index_url)[:2]
    if return_code == 1:
        team_find = re.findall('(<h3>[\s|\S]*?)<!-- / .contsbox --></div>', page)
        for team_page in team_find:
            team_name_find = re.findall("<h3>([^<]*)</h3>", team_page)
            if len(team_name_find) != 1:
                print "error team_name_find"
                continue
            team = team_name_find[0].strip()
            member_list = re.findall("<li>([\s|\S]*?)</li>", team_page)
            for member in member_list:
                member = member.replace("<br />", "").replace("\n", "").replace("\r", "").replace("\t", "")
                name_find = re.findall('''<a href="/profile/[\d]*"><img src="[^"]*" alt="[^"]*" width="120" height="150" /><span class='name_j'>([^"]*)</span><span class='name_e'>([^<]*)</span></a> ''', member)
                if len(name_find) != 1:
                    print "error name_find"
                    continue
                japanese_name, english_name = name_find[0]
                team_plus_find = re.findall('<div class="team_j">([^<]*)</div>', member)
                team_name = team
                if len(team_plus_find) == 1:
                    if team_plus_find[0].find("兼任") >= 0:
                        team_name = team + " / " + team_plus_find[0].split("/")[-1].strip().replace("兼任", "")
                japanese_name = japanese_name.replace(" ", "")
                first_name, last_name = english_name.strip().title().split(" ", 1)
                members_list.append([japanese_name, last_name + " " + first_name, team_name])
    return members_list

result = []
result += akb()
result += ske()
result += nmb()
result += hkt()
file_handle = open('member.txt', 'w')
for line in result:
    line_string = "\t".join(line)
    file_handle.write(line_string + "\n")