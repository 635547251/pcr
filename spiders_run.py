# coding:utf-8
import json
import random
from multiprocessing import Process, Queue

# import requests
# from requests.adapters import HTTPAdapter

from .spiders.logutil import init_logging, log_process_func
from .spiders.pcr_spider import pcr_spider

url = "https://www.pcrdfans.com/battle"

# 重连
# s = requests.Session()
# s.mount('http://', HTTPAdapter(max_retries=10))
# s.mount('https://', HTTPAdapter(max_retries=10))

# 随机获取ua
f = json.loads(open("pcr/spiders/ua_headers.json", "r").read())
ua_headers = []
for ua_header in f.values():
    ua_headers += ua_header
headers = {"User-Agent": random.choice(ua_headers)}


def main():
    # 日志队列
    log_q = Queue()
    # 日志子进程
    log_process = Process(target=log_process_func, args=(log_q,))
    log_process.daemon = True
    log_process.start()
    # 初始化日志设置
    init_logging(log_q)

    pcr_process = Process(target=pcr_spider, args=(log_q, url, headers))
    pcr_process.start()
    pcr_process.join()


if __name__ == '__main__':
    main()
