# -*- coding:UTF-8  -*-
# 判断存档文件中的数量和保存目录中的数量是否一致
import os


FILE_ROOT_PATH = os.path.join("photo")
SAVE_DATA_FILE_PATH = os.path.join("info/save.data")
PRIME_KEY_INDEX = 0
COUNT_INDEX = 1


# 获取指定目录下所有子目录内的文件数量
# is_integer    文件名是否是整数，如果为True，另外判断最大的那个序号是否和总文件数一致
def get_path_file_count(file_root_path, is_integer=True):
    if not os.path.exists(file_root_path):
        print "file root path %s not exist" % file_root_path
        return
    account_list = {}
    # 根目录下的所有子目录
    for dir_name in os.listdir(file_root_path):
        sub_path = os.path.join(file_root_path, dir_name)
        file_list = os.listdir(sub_path)
        total_file_count = len(file_list)
        # 如果文件名全部是整数，那么判断最大的序号是否和总数一致
        if is_integer:
            file_max_index = 0
            for file_name in file_list:
                file_max_index = max(int(file_name.split(".")[0]), file_max_index)
            if file_max_index != total_file_count:
                print "%s total count %s not equal to max count %s" % (dir_name, total_file_count, file_max_index)
        account_list[dir_name] = total_file_count
    return account_list


# 获取存档文件内的所有存档的下载数量
# prime_key_index   唯一主键的下标（列数，从0开始），需要和保存目录的文件夹名字一致
# account_index     下载数量的下标（列数，从0开始）
def get_save_data_file_count(save_data_file_path, prime_key_index, count_index):
    if not os.path.exists(save_data_file_path):
        print "save data %s not exist" % save_data_file_path
        return
    save_data_file_handle = open(save_data_file_path, "r")
    lines = save_data_file_handle.readlines()
    save_data_file_handle.close()
    account_list = {}
    for line in lines:
        temp_list = line.replace("\n", "").split("\t")
        account_list[temp_list[prime_key_index]] = temp_list[count_index]
    return account_list


if __name__ == "__main__":
    account_list_from_storage = get_path_file_count(FILE_ROOT_PATH)
    account_list_from_save_data = get_save_data_file_count(SAVE_DATA_FILE_PATH, PRIME_KEY_INDEX, COUNT_INDEX)
    for account_id in dict(account_list_from_storage):
        if account_id not in account_list_from_save_data:
            account_list_from_save_data[account_id] = 0
        if account_list_from_save_data[account_id] != account_list_from_storage[account_id]:
            print "%s count in save data: %s, in root path: %s" % (account_id, account_list_from_save_data[account_id], account_list_from_storage[account_id])
    for account_id in dict(account_list_from_storage):
        if account_id not in account_list_from_save_data:
            print "%s not found in save data" % account_id
