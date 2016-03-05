# -*- coding:UTF-8  -*-

from common import tool
import os

# fkoji
def fkoji():
    from fkoji import fkoji
    fkoji_path = os.path.join(os.path.abspath('..'), 'fkoji')
    os.chdir(fkoji_path)
    fkoji.Fkoji().main()


# # GooglePlus
def google_plus():
    from googlePlus import googlePlus
    google_plus_path = os.path.join(os.path.abspath('..'), 'googlePlus')
    os.chdir(google_plus_path)
    googlePlus.GooglePlus().main()


# # Instagram
def instagram():
    from instagram import instagram
    instagram_path = os.path.join(os.path.abspath('..'), 'instagram')
    os.chdir(instagram_path)
    instagram.Instagram().main()


# # Twitter
def twitter():
    from twitter import twitter
    twitter_path = os.path.join(os.path.abspath('..'), 'twitter')
    os.chdir(twitter_path)
    for i in range(1, 4):
        save_file_name = 'info\\save_%s.data' % i
        image_download_dir_name = 'photo\\twitter%s' % i
        save_file_path = os.path.join(twitter_path, save_file_name)
        image_download_path = os.path.join(twitter_path, image_download_dir_name)
        image_temp_path = os.path.join(image_download_path, 'tempImage')
        twitter.Twitter(save_file_path, image_download_path, image_temp_path).main()


# # Weibo
def weibo():
    from weibo import weibo
    weibo_path = os.path.join(os.path.abspath('..'), 'weibo')
    os.chdir(weibo_path)
    for save_file in ["ATF", "lunar", "save_1", "save_2", "snh48"]:
        save_file_name = "info\\%s.data" % save_file
        image_download_dir_name = "photo\\%s" % save_file
        save_file_path = os.path.join(os.path.abspath(""), save_file_name)
        image_download_path = os.path.join(os.path.abspath(""), image_download_dir_name)
        image_temp_path = os.path.join(image_download_path, "tempImage")
        weibo.Weibo(save_file_path, image_download_path, image_temp_path).main()

tool.restore_process_status()
fkoji()
google_plus()
instagram()
twitter()
weibo()
