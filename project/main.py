# -*- coding:UTF-8  -*-

import os
import sys

ROOT_PATH = os.path.abspath(os.path.dirname(sys._getframe().f_code.co_filename))


# ameblo
def ameblo():
    from ameblo import ameblo
    ameblo_path = os.path.join(ROOT_PATH, "ameblo")
    os.chdir(ameblo_path)
    ameblo.Ameblo().main()


# 半次元
def bcy():
    from bcy import bcy
    bcy_path = os.path.join(ROOT_PATH, "bcy")
    os.chdir(bcy_path)
    bcy.Bcy().main()


# 唱吧
def chang_ba():
    from changba import changba
    chang_ba_path = os.path.join(ROOT_PATH, "changba")
    os.chdir(chang_ba_path)
    changba.ChangBa().main()


# 5sing
def five_sing():
    from fiveSing import fiveSing
    five_sing_path = os.path.join(ROOT_PATH, "fiveSing")
    os.chdir(five_sing_path)
    fiveSing.FiveSing().main()


# flickr
def flickr():
    from flickr import flickr
    flickr_path = os.path.join(ROOT_PATH, "flickr")
    os.chdir(flickr_path)
    flickr.Flickr().main()


# GooglePlus
def google_plus():
    from googlePlus import googlePlus
    google_plus_path = os.path.join(ROOT_PATH, "googlePlus")
    os.chdir(google_plus_path)
    googlePlus.GooglePlus().main()


# Instagram
def instagram():
    from instagram import instagram
    instagram_path = os.path.join(ROOT_PATH, "instagram")
    os.chdir(instagram_path)
    for i in range(1, 4):
        save_data_path = os.path.join(instagram_path, "info\\save_%s.data" % i)
        image_download_path = os.path.join(instagram_path, "photo\\instagram%s" % i)
        video_download_path = os.path.join(instagram_path, "video\\instagram%s" % i)
        extra_config = {
            "save_data_path": save_data_path,
            "image_download_path": image_download_path,
            "video_download_path": video_download_path,
        }
        instagram.Instagram(extra_config).main()


# Jigadori
def jigadori():
    from jigadori import jigadori
    jigadori_path = os.path.join(ROOT_PATH, "jigadori")
    os.chdir(jigadori_path)
    jigadori.Jigadori().main()


# 欅坂46公式Blog
def keyakizaka46_diary():
    from keyakizaka46 import diary
    keyakizaka46_diary_path = os.path.join(ROOT_PATH, "keyakizaka46")
    os.chdir(keyakizaka46_diary_path)
    diary.Diary().main()


# 全面K歌
def kg():
    from kg import kg
    kg_diary_path = os.path.join(ROOT_PATH, "kg")
    os.chdir(kg_diary_path)
    kg.KG().main()


# Lofter
def lofter():
    from lofter import lofter
    lofter_path = os.path.join(ROOT_PATH, "lofter")
    os.chdir(lofter_path)
    lofter.Lofter().main()


# 美拍
def meipai():
    from meipai import meipai
    meipai_path = os.path.join(ROOT_PATH, "meipai")
    os.chdir(meipai_path)
    meipai.MeiPai().main()


# 美图录
def meitulu():
    from meitulu import meitulu
    meitulu_path = os.path.join(ROOT_PATH, "meitulu")
    os.chdir(meitulu_path)
    meitulu.MeiTuLu().main()


# 美图赚赚
def meituzz():
    from meituzz import meituzz
    meituzz_path = os.path.join(ROOT_PATH, "meituzz")
    os.chdir(meituzz_path)
    meituzz.MeiTuZZ().main()


# 秒拍
def miaopai():
    from miaopai import miaopai
    miaopai_path = os.path.join(ROOT_PATH, "miaopai")
    os.chdir(miaopai_path)
    miaopai.MiaoPai().main()


# 7gogo
def nana_go_go():
    from nanaGoGo import nanaGoGo
    nana_go_go_path = os.path.join(ROOT_PATH, "nanaGoGo")
    os.chdir(nana_go_go_path)
    nanaGoGo.NanaGoGo().main()


# 网易摄影
def netease_photographer():
    from netEase import photographer
    netease_photographer_path = os.path.join(ROOT_PATH, "netEase")
    os.chdir(netease_photographer_path)
    photographer.Photographer().main()


# 乃木坂46公式Blog
def nogizaka46_blog():
    from nogizaka46 import blog
    nogizaka46_log_path = os.path.join(ROOT_PATH, "nogizaka46")
    os.chdir(nogizaka46_log_path)
    blog.Blog().main()


# nvshens
def nvshens():
    from nvshens import nvshens
    nvshens_log_path = os.path.join(ROOT_PATH, "nvshens")
    os.chdir(nvshens_log_path)
    nvshens.Nvshens().main()


# 篠田麻里子blog
def shinoda_blog():
    from shinoda import shinoda
    shinoda_blog_path = os.path.join(ROOT_PATH, "shinoda")
    os.chdir(shinoda_blog_path)
    shinoda.Blog().main()


# 图虫
def tuchong():
    from tuchong import tuchong
    tuchong_path = os.path.join(ROOT_PATH, "tuchong")
    os.chdir(tuchong_path)
    tuchong.TuChong().main()


# tumblr
def tumblr():
    from tumblr import tumblr
    tumblr_path = os.path.join(ROOT_PATH, "tumblr")
    os.chdir(tumblr_path)
    tumblr.Tumblr().main()


# # Twitter
def twitter():
    from twitter import twitter
    twitter_path = os.path.join(ROOT_PATH, "twitter")
    os.chdir(twitter_path)
    for i in range(1, 6):
        save_data_path = os.path.join(twitter_path, "info\\save_%s.data" % i)
        image_download_path = os.path.join(twitter_path, "photo\\twitter%s" % i)
        video_download_path = os.path.join(twitter_path, "video\\twitter%s" % i)
        extra_config = {
            "save_data_path": save_data_path,
            "image_download_path": image_download_path,
            "video_download_path": video_download_path,
        }
        twitter.Twitter(extra_config).main()


# # 微博
def weibo():
    from weibo import weibo
    weibo_path = os.path.join(ROOT_PATH, "weibo")
    os.chdir(weibo_path)
    for save_file in ["ATF", "lunar", "save_1", "save_2", "snh48"]:
        save_data_path = os.path.join(weibo_path, "info\\%s.data" % save_file)
        image_download_path = os.path.join(weibo_path, "photo\\%s" % save_file)
        # video_download_path = os.path.join(weibo_path, "video\\%s" % save_file)
        extra_config = {
            "save_data_path": save_data_path,
            "image_download_path": image_download_path,
            # "video_download_path": video_download_path,
        }
        weibo.Weibo(extra_config).main()


# 微博文章
def weibo_article():
    from weibo import article
    weibo_article_path = os.path.join(ROOT_PATH, "weibo")
    os.chdir(weibo_article_path)
    extra_config = {
        "save_data_path": os.path.join(weibo_article_path, "info\\article.data"),
        "image_download_path": os.path.join(weibo_article_path, "article"),
    }
    article.Article(extra_config).main()


# 一直播
def yizhibo():
    from yizhibo import yizhibo
    yizhibo_path = os.path.join(ROOT_PATH, "yizhibo")
    os.chdir(yizhibo_path)
    yizhibo.YiZhiBo().main()


# 尤物看板
def ywkb():
    from ywkb import ywkb
    ywkb_path = os.path.join(ROOT_PATH, "ywkb")
    os.chdir(ywkb_path)
    ywkb.YWKB().main()


# ameblo()
# bcy()
# chang_ba()
# five_sing()
# flickr()
# google_plus()
# instagram()
# jigadori()
# keyakizaka46_diary()
# kg()
# lofter()
# meipai()
# meitulu()
# meituzz()
# miaopai()
# nana_go_go()
# netease_photographer()
# nogizaka46_blog()
# nvshens()
# shinoda_blog()
# tuchong()
# tumblr()
# twitter()
# weibo()
# weibo_article()
# yizhibo()
# ywkb()
# tool.shutdown()
