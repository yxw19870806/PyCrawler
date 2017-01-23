# -*- coding:UTF-8  -*-
from common import net, tool
import re

item_list = {
    "helm": "头盔",
    "spirit-stone": "炼气石",
    "voodoo-mask": "巫毒面具",
    "wizard-hat": "秘术帽",
    "pauldrons": "护肩",
    "chest-armor": "胸甲",
    "cloak": "斗篷",
    "bracers": "护腕",
    "gloves": "手套",
    "belt": "腰带",
    "mighty-belt": "重型腰带",
    "pants": "裤子",
    "boots": "鞋子",
    "amulet": "护身符",
    "ring": "戒指",
    "shield": "盾",
    "mojo": "咒物",
    "orb": "法器",
    "quiver": "箭筒",
    "enchantress-focus": "巫女法器",
    "scoundrel-token": "盗贼道具",
    "templar-relic": "骑士圣物",
    "axe-1h": "斧",
    "dagger": "匕首",
    "mace-1h": "钉锤",
    "spear": "矛",
    "sword-1h": "剑",
    "ceremonial-knife": "祭祀刀",
    "fist-weapon": "拳套武器",
    "mighty-weapon-1h": "重型武器",
    "flail1-1h": "连枷",
    "axe-2h": "双手斧",
    "mace-2h": "双手钉锤",
    "polearm": "长柄武器",
    "staff": "法杖",
    "sword-2h": "双手剑",
    "daibo": "武杖",
    "mighty-weapon-2h": "双手重型武器",
    "flail2-2h": "双手连枷",
    "legendarygem": "傳奇宝石",
}

item_attribute_list = {}
base_host = "http://db.d.163.com"
for item_path, item_position in item_list.items():
    page_count = 1
    item_attribute_list[item_path] = []
    while True:
        if item_position == "傳奇宝石":
            item_index_url = base_host + "/tw/base/legendarygem/"
        else:
            item_index_url = base_host + "/tw/item/%s/legendary.html#page=%s" % (item_path, page_count)
        item_index_page_response = net.http_request(item_index_url)
        if item_index_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            # item_index = item_index.decode("utf-8")
            item_index_page = tool.find_sub_string(item_index_page_response.data, '<div class="cizhui-c-m', '<div class="data-options', 1)
            item_index_page = item_index_page.decode("GBK").encode("utf-8")
            item_info_list = re.findall('<tr class="[\s|\S]*?</tr>', item_index_page)
            if len(item_info_list) == 0:
                continue
            for item_info in item_info_list:
                if item_info.find('<em class="transmog-s"></em>') >= 0:
                    continue
                item_page_url = tool.find_sub_string(item_info, '<a href="', '"')
                item_name = tool.find_sub_string(item_info, 'class="diablo3tip">', "</a>")
                item_name = item_name.replace("'", "’")
                item_page_url = base_host + item_page_url
                item_page_response = net.http_request(item_page_url)
                if item_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
                    item_detail = tool.find_sub_string(item_page_response.data, '<div class="content-right-bdl clearfix">', '<dl class="content-right-bdr">')
                    item_detail = item_detail.decode("GBK").encode("utf-8")
                    attribute = tool.find_sub_string(item_detail, "<!-- 主要属性-->", "<!-- 华丽丽的分割线 -->").strip()
                    special_attribute = tool.find_sub_string(attribute, '<li class="d3-color-orange">', "</li>")
                    if special_attribute:
                        special_attribute = special_attribute[special_attribute.find(">") + 1:]
                        special_attribute = special_attribute.replace("</span>", "").replace('<span class="d3-color-magic">', "").replace('<span class="value">', "")
                        special_attribute = special_attribute.replace("'", "’")
                    item_introduction = tool.find_sub_string(item_detail, '<div class="item-flavor d3-color-orange serif">', "</div>").strip()
                    item_introduction = item_introduction.replace("'", "’")
                    print item_position, item_name, special_attribute, item_introduction
                    item_attribute_list[item_path].append([item_name, special_attribute, item_introduction])
                else:
                    print "error get" + item_page_url
        else:
            print "error get" + item_index_url
        pagination = tool.find_sub_string(item_index_page_response.data, '<ul class="ui-pagination">', "</ul>")
        if pagination:
            pagination = re.findall('<a href="#page=([\d]*)">', pagination)
            max_page = 1
            for page in pagination:
                max_page = max(max_page, int(page))
            if page_count < max_page:
                page_count += 1
                continue
        break


tool.make_dir("data", 0)
for item_path in item_attribute_list:
    file_handle = open(tool.change_path_encoding("data\%s.txt" % item_list[item_path]), "w")
    for item in item_attribute_list[item_path]:
        file_handle.write("\t".join(item) + "\n")
    file_handle.close()
