# -*- coding:UTF-8  -*-
"""
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import hashlib
import os
import time

buff_size = 1024 * 1024 * 4  # 读取4MB


def md5(source_file_path):
    pos = 0
    file_handle = open(source_file_path, "rb")
    file_hash = hashlib.md5()
    while True:
        # 从文件中读取一段内容
        file_handle.seek(pos)
        buff_byte = file_handle.read(buff_size)
        if not buff_byte:
            break
        file_hash.update(buff_byte)
        # 计算取下一段内容长度
        pos += buff_size
        time.sleep(0.1)
    return str(file_hash.hexdigest())


class GetPathMd5List():
    def __init__(self, root_path):
        self.root_path = root_path
        self.result = {}

    def scan_path(self):
        self._scan_path(self.root_path)
        return self

    def get_result(self):
        return self.result

    # 生成目录下全部文件的md5码
    def _scan_path(self, source_dir):
        for file_name in os.listdir(source_dir):
            file_path = os.path.join(source_dir, file_name)
            if os.path.isdir(file_path):
                self._scan_path(file_path)
            else:
                print "start md5: " + file_path
                self.result[file_path.replace(self.root_path, "")] = md5(file_path)


if __name__ == "__main__":
    path = ""
    result = GetPathMd5List(path).scan_path().get_result()
    print result
