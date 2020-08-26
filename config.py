DB_USERNAME = "root"
DB_PASSWORD = "123456789"
DB_HOSTNAME = "127.0.0.1"
DB_DATABASE = "PCR"


# 日志配置参数
log_encoding = "UTF-8"
log_dir_path = "pcr/spiders/log"
log_name = "spider.log"
# 日志级别: DEBUG, INFO, WARNING, ERROR, FATAL
log_level = "INFO"

common_wait_time = 3  # 通用等待时间

# 需要爬取的角色
ch_whitelist = [
    "羊驼", "布丁", "空花", "黑骑", "狗拳", "佩可", "望", "狼", "裁缝", "猫剑", "水吃", "铃铛", "姐姐", "兔兔", "黄骑", "毛二力", "扇子", "yly", "充电宝", "中二", "妈", "水妈", "深月", "妹法", "yls", "妹弓", "暴击弓", "tp弓", "老师", "圣母", "黑猫", "初音", "大眼", "水女仆", "真步", "镜子", "xcw"
]


# 阵型必须要的主T
main_tank = ["羊驼", "布丁", "空花", "望"]


# 其他角色
other_list = [
    "黑骑", "佩可", "猫剑", "水吃", "铃铛", "姐姐", "黄骑", "毛二力", "扇子", "yly", "充电宝", "水妈", "深月", "妹法", "tp弓", "初音", "大眼", "真步", "镜子", "xcw"
]


pos2ch_dic = {
    "-206.667px -310px": "羊驼",
    "0px -103.333px": "布丁",
    "-310px -155px": "空花",
    "-310px -258.333px": "黑骑",
    "-206.667px 0px": "狗拳",
    "-361.667px -155px": "佩可",
    "-258.333px -51.6667px": "望",
    "-310px -51.6667px": "狼",
    "-258.333px -206.667px": "哈哈剑",
    "-310px -310px": "裁缝",
    "-51.6667px 0px": "猫拳",
    "-51.6667px -51.6667px": "炸弹人",
    "-51.6667px -206.667px": "熊锤",
    "-310px -206.667px": "猫剑",
    "-206.667px -206.667px": "病娇",
    "-258.333px -361.667px": "水吃",
    "-206.667px -155px": "铃铛",
    "-361.667px -103.333px": "吉他",
    "0px -51.6667px": "剑圣",
    "-51.6667px -310px": "姐姐",
    "-206.667px -103.333px": "兔兔",
    "-258.333px -155px": "忍",
    "0px -258.333px": "奶牛",
    "-51.6667px -258.333px": "黄骑",
    "-258.333px -310px": "毛二力",
    "-258.333px -103.333px": "扇子",
    "0px -310px": "子龙",
    "-310px -103.333px": "yly",
    "-258.333px 0px": "充电宝",
    "-103.333px -103.333px": "中二",
    "-361.667px -206.667px": "妈",
    "0px 0px": "水妈",
    "-155px -206.667px": "松鼠",
    "-155px -310px": "深月",
    "-103.333px -51.6667px": "妹法",
    "0px -206.667px": "姐法",
    "0px -361.667px": "yls",
    "-155px -51.6667px": "妹弓",
    "-155px -155px": "暴击弓",
    "-206.667px -258.333px": "tp弓",
    "-206.667px -51.6667px": "老师",
    "-103.333px -206.667px": "女仆",
    "-103.333px -155px": "圣母",
    "-361.667px -258.333px": "黑猫",
    "-155px -103.333px": "初音",
    "-103.333px -310px": "大眼",
    "-361.667px -361.667px": "水女仆",
    "-258.333px -258.333px": "香菜弓",
    "-310px 0px": "千歌",
    "-155px 0px": "真步",
    "-206.667px -361.667px": "ue",
    "-51.6667px -103.333px": "镜子",
    "-103.333px -258.333px": "xcw"
}


pos2ch_6x_dic = {
    "0px -155px": "羊驼",
    "-51.6667px -155px": "佩可",
    "-51.6667px 0px": "猫拳",
    "-51.6667px -103.333px": "熊锤",
    "-155px 0px": "猫剑",
    "0px -51.6667px": "剑圣",
    "-155px -103.333px": "姐姐",
    "0px 0px": "黄骑",
    "-155px -51.6667px": "子龙",
    "-103.333px -155px": "妈",
    "-103.333px 0px": "妹弓",
    "0px -103.333px": "老师",
    "-155px -155px": "黑猫",
    "-103.333px -51.6667px": "初音",
    "-51.6667px -51.6667px": "真步",
    "-103.333px -103.333px": "ue"
}

ranking = 10  # 获取排名前n名数据
