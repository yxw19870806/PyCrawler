# -*- coding:UTF-8  -*-

from common import tool
import os

# ameblo
def ameblo():
    from ameblo import ameblo
    ameblo_path = os.path.join(os.path.abspath(".."), "ameblo")
    os.chdir(ameblo_path)
    ameblo.Ameblo().main()


# 半次元
def bcy():
    from bcy import bcy
    bcy_path = os.path.join(os.path.abspath(".."), "bcy")
    os.chdir(bcy_path)
    bcy.Bcy().main()


# 唱吧
def chang_ba():
    from changba import changba
    chang_ba_path = os.path.join(os.path.abspath(".."), "chang_ba")
    os.chdir(chang_ba_path)
    changba.ChangBa().main()


# fkoji
def fkoji():
    from fkoji import fkoji
    fkoji_path = os.path.join(os.path.abspath(".."), "fkoji")
    os.chdir(fkoji_path)
    fkoji.Fkoji().main()


# GooglePlus
def google_plus():
    from googlePlus import googlePlus
    google_plus_path = os.path.join(os.path.abspath(".."), "googlePlus")
    os.chdir(google_plus_path)
    googlePlus.GooglePlus().main()


# Instagram
def instagram():
    from instagram import instagram
    instagram_path = os.path.join(os.path.abspath(".."), "instagram")
    os.chdir(instagram_path)
    for i in range(1, 4):
        save_file_name = "info\\save_%s.data" % i
        image_download_dir_name = "photo\\instagram%s" % i
        save_data_path = os.path.join(instagram_path, save_file_name)
        image_download_path = os.path.join(instagram_path, image_download_dir_name)
        image_temp_path = os.path.join(image_download_path, "tempImage")
        video_download_dir_name = "video\\instagram%s" % i
        video_download_path = os.path.join(os.path.abspath(""), video_download_dir_name)
        video_temp_path = os.path.join(video_download_path, "tempVideo")
        extra_config = {
            "save_data_path": save_data_path,
            "image_download_path": image_download_path,
            "image_temp_path": image_temp_path,
            "video_download_path": video_download_path,
            "video_temp_path": video_temp_path,
        }
        instagram.Instagram(extra_config).main()


# 欅坂46公式Blog
def keyakizaka46_diary():
    from keyakizaka46 import diary
    keyakizaka46_diary_path = os.path.join(os.path.abspath(".."), "keyakizaka46")
    os.chdir(keyakizaka46_diary_path)
    diary.Diary().main()


# Lofter
def lofter():
    from lofter import lofter
    lofter_path = os.path.join(os.path.abspath(".."), "lofter")
    os.chdir(lofter_path)
    lofter.Lofter().main()


# 美拍
def meipai():
    from meipai import meipai
    meipai_path = os.path.join(os.path.abspath(".."), "meipai")
    os.chdir(meipai_path)
    meipai.MeiPai().main()


# 秒拍
def miaopai():
    from miaopai import miaopai
    miaopai_path = os.path.join(os.path.abspath(".."), "miaopai")
    os.chdir(miaopai_path)
    miaopai.MiaoPai().main()


# 7gogo
def nana_go_go():
    from nanaGoGo import nanaGoGo
    nana_go_go_path = os.path.join(os.path.abspath(".."), "nanaGoGo")
    os.chdir(nana_go_go_path)
    nanaGoGo.NanaGoGo().main()


# 乃木坂46公式Blog
def nogizaka46_blog():
    from nogizaka46 import blog
    nogizaka46_log_path = os.path.join(os.path.abspath(".."), "nogizaka46")
    os.chdir(nogizaka46_log_path)
    blog.Blog().main()


# 图虫
def tuchong():
    from tuchong import tuchong
    tuchong_path = os.path.join(os.path.abspath(".."), "tuchong")
    os.chdir(tuchong_path)
    tuchong.TuChong().main()


# tumblr
def tumblr():
    from tumblr import tumblr
    tumblr_path = os.path.join(os.path.abspath(".."), "tumblr")
    os.chdir(tumblr_path)
    tumblr.Tumblr().main()


# # Twitter
def twitter():
    from twitter import twitter
    twitter_path = os.path.join(os.path.abspath(".."), "twitter")
    os.chdir(twitter_path)
    for i in range(1, 5):
        save_file_name = "info\\save_%s.data" % i
        image_download_dir_name = "photo\\twitter%s" % i
        save_data_path = os.path.join(twitter_path, save_file_name)
        image_download_path = os.path.join(twitter_path, image_download_dir_name)
        image_temp_path = os.path.join(image_download_path, "tempImage")
        video_download_dir_name = "video\\twitter%s" % i
        video_download_path = os.path.join(os.path.abspath(""), video_download_dir_name)
        video_temp_path = os.path.join(video_download_path, "tempVideo")
        extra_config = {
            "save_data_path": save_data_path,
            "image_download_path": image_download_path,
            "image_temp_path": image_temp_path,
            "video_download_path": video_download_path,
            "video_temp_path": video_temp_path,
        }
        twitter.Twitter(extra_config).main()


# # 微博
def weibo():
    from weibo import weibo
    weibo_path = os.path.join(os.path.abspath(".."), "weibo")
    os.chdir(weibo_path)
    for save_file in ["ATF", "lunar", "save_1", "save_2", "snh48"]:
        save_file_name = "info\\%s.data" % save_file
        image_download_dir_name = "photo\\%s" % save_file
        save_data_path = os.path.join(os.path.abspath(""), save_file_name)
        image_download_path = os.path.join(os.path.abspath(""), image_download_dir_name)
        image_temp_path = os.path.join(image_download_path, "tempImage")
        video_download_dir_name = "video\\%s" % save_file
        video_download_path = os.path.join(os.path.abspath(""), video_download_dir_name)
        video_temp_path = os.path.join(video_download_path, "tempVideo")
        extra_config = {
            "save_data_path": save_data_path,
            "image_download_path": image_download_path,
            "image_temp_path": image_temp_path,
            "video_download_path": video_download_path,
            "video_temp_path": video_temp_path,
        }
        weibo.Weibo(extra_config).main()


# 一直播
def yizhibo():
    from yizhibo import yizhibo
    yizhibo_path = os.path.join(os.path.abspath(".."), "yizhibo")
    os.chdir(yizhibo_path)
    yizhibo.YiZhiBo().main()


ameblo()
bcy()
google_plus()
chang_ba()
instagram()
keyakizaka46_diary()
lofter()
meipai()
miaopai()
nana_go_go()
nogizaka46_blog()
tumblr()
tuchong()
twitter()
weibo()
yizhibo()
fkoji()
# tool.shutdown()
