# -*- coding:UTF-8  -*-
from common import tool
import re


def akb(file_handle):
    for team_id in [1, 2, 3, 4, 12, 15]:
        index_url = "http://www.akb48.co.jp/about/members/?team_id=" + str(team_id)
        return_code, page = tool.http_request(index_url)[:2]
        if return_code == 1:
            member_list_page = tool.find_sub_string(page, '<ul class="memberListUl">', '</ul>')
            if member_list_page:
                member_list = re.findall("<li>([\s|\S]*?)</li>", member_list_page)
                for member in member_list:
                    member = member.replace("<br />", "").replace("\n", "").replace("\r", "").replace("\t", "")
                    japanese_name = tool.find_sub_string(member, '<h4 class="memberListNamej">', '</h4>')
                    english_name = tool.find_sub_string(member, '<p class="memberListNamee">', '</p>')
                    team_find = re.findall('<h5 class="memberListTeam">([^<]*)</h5>', member)
                    if not japanese_name:
                        print "error japanese_name"
                        continue
                    if not english_name:
                        print "error english_name"
                        continue
                    if (team_id != 12 and len(team_find) != 1) or (team_id == 12 and len(team_find) != 2):
                        print "error team_find"
                        continue

                    japanese_name = japanese_name.replace(" ", "")
                    first_name, last_name = english_name.split(" ", 1)
                    team = team_find[0].strip().replace("  /", " / ")

                    file_handle.write(japanese_name + "\t" + last_name + " " + first_name + "\t" + team + "\n")
            else:
                print "error member_list_page"


def ske(file_handle):
    split_list = {
        "SKE48 Team S": ("<!-- LIST - TEAM S -->", "<!-- //LIST - TEAM S -->"),
        "SKE48 Team KII": ("<!-- LIST - TEAM KII -->", "<!-- //LIST - TEAM KII -->"),
        "SKE48 Team E": ("<!-- LIST - TEAM E -->", "<!-- //LIST - TEAM E -->"),
        "SKE48 Team Kenkyusei": ("<!-- LIST - KENKYUSEI -->", "<!-- //LIST - KENKYUSEI -->")
    }
    index_url = "http://www.ske48.co.jp/profile/list.php"
    return_code, page = tool.http_request(index_url)[:2]
    if return_code == 1:
        for team_name in split_list:
            team_page = tool.find_sub_string(page, split_list[team_name][0], split_list[team_name][1])
            member_list = re.findall('<dl>([\s|\S]*?)</dl>', team_page)
            for member in member_list:
                member = member.replace("<br />", "").replace("\n", "").replace("\r", "").replace("\t", "")
                japanese_name_find = re.findall('<h3><a href="./\?id=[^"]*">([^<]*)</a></h3>', member)
                english_name = tool.find_sub_string(member, '<h3 class="en">', '</h3>')
                plus_text = tool.find_sub_string(member, '<li class="textPlus">', '</li>')
                if len(japanese_name_find) != 1:
                    print "error japanese_name_find"
                    continue
                if not english_name:
                    print "error english_name"
                    continue

                japanese_name = japanese_name_find[0].replace(" ", "")
                first_name, last_name = english_name.strip().title().split(" ", 1)
                if plus_text and plus_text.find("兼任") > 0:
                    team = team_name + " / " + plus_text.split("/")[-1].strip().replace("チーム", " Team ").replace("兼任", "")
                else:
                    team = team_name

                file_handle.write(japanese_name + "\t" + last_name + " " + first_name + "\t" + team + "\n")


def nmb(file_handle):
    team_list = {
        "teamn": "NMB48 Team N",
        "teamm": "NMB48 Team M",
        "teamb2": "NMB48 Team BII",
        "dkenkyusei": "NMB48 Team Kenkyusei",
        "kenkyusei": "NMB48 Team Kenkyusei",
    }
    index_url = "http://www.nmb48.com/member/"
    return_code, page = tool.http_request(index_url)[:2]
    if return_code == 1:
        team_page_list = re.findall('<!--▼チーム別領域ボックス▼-->([\s|\S]*?)<!--▲チーム別領域ボックス▲--> ', page)
        for team_page in team_page_list:
            team_find = tool.find_sub_string(team_page, '<a name="', '"></a>')
            if team_find:
                if team_find not in team_list:
                    print "not found " + team_find + " in team_list"
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

                    team = team_list[team_find]
                    if english_name_find[0].find("<span>") >= 0:
                        temp = english_name_find[0].split("<span>")
                        english_name_find[0] = temp[0]
                        temp[1] = temp[1].replace("</span>", "")
                        if temp[1].find("研究生") == -1:
                            team += " / " + temp[1].split("/")[-1].strip()
                    japanese_name = japanese_name_find[0].replace("　", " ").replace(" ", "")
                    first_name, last_name = english_name_find[0].strip().title().split(" ", 1)

                    file_handle.write(japanese_name + "\t" + last_name + " " + first_name + "\t" + team + "\n")
            else:
                print "error team_find"


def hkt(file_handle):
    index_url = "http://www.hkt48.jp/profile/"
    return_code, page = tool.http_request(index_url)[:2]
    if return_code == 1:
        team_find = re.findall('(<h3>[\s|\S]*?)<!-- / .contsbox --></div>', page)
        for team_page in team_find:
            team = tool.find_sub_string(team_page, "<h3>", "</h3>")
            if not team:
                print "error team"
                continue
            team = team.strip()
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

                file_handle.write(japanese_name + "\t" + last_name + " " + first_name + "\t" + team_name + "\n")


def jkt(file_handle):
    members_list = []
    index_url = "http://www.jkt48.com/member/list"
    return_code, page = tool.http_request(index_url)[:2]
    if return_code == 1:
        page = tool.find_sub_string(page, '<div id="mainCol">', "<!--end #mainCol-->", 1)
        start_index = 0
        start_index_list = []
        while start_index != -1:
            start_index = page.find('<a name="', start_index + 1)
            start_index_list.append(start_index)
        for i in range(0, len(start_index_list) - 1):
            start = start_index_list[i]
            end = start_index_list[i + 1]
            if end == -1:
                end = len(page)
            split_page = page[start: end]
            team_name = tool.find_sub_string(split_page, "<h2>", "</h2>")
            if team_name.find("Team") == -1:
                team_name = "Team kenkyusei"
            team_name = "JKT48 " + team_name
            member_list = re.findall('<div class="profileWrap">([\s|\S]*?)</div><!--/loop-->',split_page)
            for member in member_list:
                member = member.replace("<br>", "").replace("\n", "").replace("\r", "").replace("\t", "")
                japanese_name = english_name = tool.find_sub_string(member, 'alt="', '"')

                file_handle.write(japanese_name + "\t" + english_name + "\t" + team_name + "\n")


def main():
    file_handle = open('member.txt', 'w')
    akb(file_handle)
    ske(file_handle)
    nmb(file_handle)
    hkt(file_handle)
    jkt(file_handle)
    file_handle.close()

if __name__ == "__main__":
    main()
