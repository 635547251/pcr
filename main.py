# coding:utf-8
import glob
import json
import os
from collections import defaultdict
from multiprocessing import Manager, Process

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import ticker

from .config import data_path, proc_pool_size, ranking
from .db import get_pcr_team

with open("pcr/conf/ch.json", "r", encoding="utf-8") as f:
    d = json.load(f)
    main_tank = d["main_tank"]
    other_list = d["other_list"]
    all_ch_num = len(d["pos2ch_dic"])


# 这两行代码解决 plt 中文显示的问题
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


def get_ch_attend_and_win(pcr_team: list[tuple[str]]) -> dict[str, tuple[dict[str, str]]]:
    '''
    统计1-4人组合出场率, 胜率
    :param  pcr_team            数据库查询结果
    :return ch_attend_and_time  各组合的xy轴字典
    '''
    def backtrace(t_list: list[str], output_1: defaultdict[int],
                  output_2: defaultdict[int], output_3: defaultdict[int],
                  output_4: defaultdict[int], i=0, res=[]):
        '''
        获取所有人物组合
        '''
        if len(res) >= 1:
            k = "|".join(res)
            if len(res) == 1:
                output_1[k] += 1
            elif len(res) == 2:
                output_2[k] += 1
            elif len(res) == 3:
                output_3[k] += 1
            else:
                output_4[k] += 1
                return
        for j in range(i, len(t_list)):
            backtrace(t_list, output_1, output_2, output_3,
                      output_4, j + 1, res + [t_list[j]])

    team = set()
    # 出场次数
    ch_1_attend_time, ch_2_attend_time = defaultdict(int), defaultdict(int)
    ch_3_attend_time, ch_4_attend_time = defaultdict(int), defaultdict(int)
    # 胜利次数 失败次数
    ch_1_win_time, ch_1_lose_time = defaultdict(int), defaultdict(int)
    ch_2_win_time, ch_2_lose_time = defaultdict(int), defaultdict(int)
    ch_3_win_time, ch_3_lose_time = defaultdict(int), defaultdict(int)
    ch_4_win_time, ch_4_lose_time = defaultdict(int), defaultdict(int)
    for attack_team, defense_team, _, _ in pcr_team:
        # 统计进攻队
        if attack_team not in team:
            team.add(attack_team)
            backtrace(attack_team.split("|"), ch_1_attend_time, ch_2_attend_time,
                      ch_3_attend_time, ch_4_attend_time)
        backtrace(attack_team.split("|"), ch_1_win_time,
                  ch_2_win_time, ch_3_win_time, ch_4_win_time)
        # 统计防守队
        if defense_team not in team:
            team.add(defense_team)
            backtrace(defense_team.split("|"), ch_1_attend_time, ch_2_attend_time,
                      ch_3_attend_time, ch_4_attend_time)
        backtrace(defense_team.split("|"), ch_1_lose_time,
                  ch_2_lose_time, ch_3_lose_time, ch_4_lose_time)

    ch_attend_and_time = {
        "1": (ch_1_attend_time, ch_1_win_time, ch_1_lose_time),
        "2": (ch_2_attend_time, ch_2_win_time, ch_2_lose_time),
        "3": (ch_3_attend_time, ch_3_win_time, ch_3_lose_time),
        "4": (ch_4_attend_time, ch_4_win_time, ch_4_lose_time)
    }
    return ch_attend_and_time


def get_ch_attend_and_win_chart(pcr_team: list[tuple[str]]):
    '''
    获取各角色出场率胜率图表
    :param  pcr_team    数据库查询结果
    '''
    def get_axis(ch_attend_time: dict[str, int], ch_win_time: dict[str, int],
                 ch_lose_time: dict[str, int]) -> tuple[list]:
        '''
        获取xy轴数据
        :param  ch_attend_time  出场次数
        :param  ch_win_time     胜率次数
        :parma  ch_lose_time    失败次数
        :return y_axis          y轴 角色
        :return x_axis1         x轴1 出场率
        :return x_axis2         x轴2 胜率
        '''
        team_len = len(set(pcr_team))
        ch_attend_rate = sorted(
            {k: round(v / team_len, 4)
             for k, v in ch_attend_time.items()}.items(),
            key=lambda x: x[1])[-ranking:]
        z = list(zip(*ch_attend_rate))
        y_axis, x_axis1 = z[0], z[1]  # y轴 角色  x轴1 出场率
        x_axis2 = [round(ch_win_time[ch] / (ch_win_time[ch] + ch_lose_time[ch]), 4)
                   for ch in y_axis][::-1]  # x轴2 胜率

        return y_axis, x_axis1, x_axis2

    def generate_chart(y_axis: list[str], x_axis1: list[str],
                       x_axis2: list[str], title: str, height=0.8, n=2):
        '''
        生成各角色出场率胜率图表
        :param  y_axis  y轴 角色
        :param  x_axis1 x轴1 出场率
        :param  x_axis2 x轴2 胜率
        :param  title   图标标题
        :param  height  条状图总宽度
        :param  n       条状图总个数
        '''
        def to_percent(temp, position):
            return "%1.0f" % (100 * temp) + "%"

        y_pos = height / n ** 2
        plt.barh(np.arange(len(y_axis)) + y_pos, x_axis1,
                 height=y_pos, color="r",  alpha=0.8, label="出场率")
        plt.barh(np.arange(len(y_axis)) - y_pos, x_axis2,
                 height=y_pos, color="g", alpha=0.7, label="胜率")

        plt.title(title)  # 标题
        plt.yticks(range(ranking), y_axis)  # y轴标签

        plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(to_percent))  # x轴坐标显示百分百
        plt.xlim([0, 1])  # x轴坐标范围

        # 为每个条形图添加数值标签
        for x, y in enumerate(x_axis1):
            plt.text(y + 0.01, x + y_pos,
                     "{:.2%}".format(y), va="center", ha="left", label="出场率")
        for x, y in enumerate(x_axis2):
            plt.text(y + 0.01, x - y_pos,
                     "{:.2%}".format(y), va="center", ha="left", label="出场率")

    fig = plt.figure(figsize=(16, 8))
    fig.canvas.set_window_title("pcr国服各角色出场率TOP%s及胜率" % ranking)  # 窗口名
    fig.subplots_adjust(left=0.1, right=0.97, top=0.95,
                        bottom=0.05, wspace=0.3)  # 子图间距
    # fig.tight_layout()  # 自动调整标签

    # 各角色
    ch_attend_and_win = get_ch_attend_and_win(pcr_team)
    plt.subplot(221)
    generate_chart(*get_axis(*ch_attend_and_win["1"]), title="各个角色")
    fig.legend(loc="upper right")  # 标签
    # 2人组合
    plt.subplot(222)
    generate_chart(*get_axis(*ch_attend_and_win["2"]), title="2人组合")
    # 3人组合
    plt.subplot(223)
    generate_chart(*get_axis(*ch_attend_and_win["3"]), title="3人组合")
    # 4人组合
    plt.subplot(224)
    generate_chart(*get_axis(*ch_attend_and_win["4"]), title="4人组合")

    plt.show()


def get_mypjjc_team(pcr_team: list[tuple[str]]):
    '''
    获取我的pjjc所有阵容
    :param  pcr_team    数据库查询结果
    :return data        我的所有阵容
    '''
    def backtrace(n: int, t_list: list[str], fd, i=0, res=[]):
        if len(res) == n:
            d = {r: all_team[r] for r in res}
            print(str(d), file=fd)
            return
        else:
            for j in range(i, len(t_list)):
                if res:
                    # 去除重复角色
                    for ch in t_list[j].split("|"):
                        if ch in "|".join(res):
                            break
                    else:
                        backtrace(n, t_list, fd, j + 1, res + [t_list[j]])
                else:
                    backtrace(n, t_list, fd, j + 1, res + [t_list[j]])

    def chunkify(filename: str, file_end: int, size=100*1024*1024):
        '''
        分块切割文件
        :param filename 文件名
        :param file_end 文件游标尾
        :return         游标头 游标尾
        '''
        with open(filename, 'rb') as f:
            chunk_end = f.tell()
            while True:
                chunk_start = chunk_end
                f.seek(size, 1)
                f.readline()
                chunk_end = f.tell()
                yield chunk_start, chunk_end - chunk_start
                if chunk_end > file_end:
                    break

    # 获取我的所有pjjc阵容记录
    _main_tank, my_chlist = set(main_tank), set(main_tank + other_list)
    # 所有进攻角色、重复进攻角色、总好评、总差评
    all_team = defaultdict(lambda: ([set(), None, 0, 0]))
    for attack_team, defense_team, good_comment, bad_comment in pcr_team:
        d_sp = defense_team.split("|")
        for ch in d_sp:
            if ch not in my_chlist or d_sp[-1] not in _main_tank:
                break
        else:
            a_sp = attack_team.split("|")
            all_team[defense_team][0].update(a_sp)
            all_team[defense_team][1] = set(
                a_sp) if all_team[defense_team][1] is None else all_team[defense_team][1] & set(a_sp)
            all_team[defense_team][2] += good_comment
            all_team[defense_team][3] += bad_comment

    # TODO 回溯算法优化 大数据存储
    filename = os.path.join(data_path, "data.txt")
    with open(filename, "w") as fd:
        backtrace(3, list(all_team.keys()), fd)

    # 分块切割文件
    file_end = os.path.getsize(filename)
    with open(filename, "rb") as f:
        for index, (chunk_start, size) in enumerate(chunkify(filename, file_end)):
            f.seek(chunk_start)
            lines = f.read(size).splitlines()
            with open(os.path.join(data_path, "data" + str(index) + ".txt"), "w") as fd:
                for line in lines:
                    print(line.decode("utf-8"), file=fd)


def get_bad_comment_rate(obj: list[list[str, int, int]]) -> float:
    '''
    获取p场队伍总差评率
    :param obj  p场队伍列表
    :return     差评率
    '''
    sum_gc_bc = obj[0][2] + obj[1][2] + \
        obj[2][2] + obj[0][1] + obj[1][1] + obj[2][1]
    return ((obj[0][2] + obj[1][2] + obj[2][2]) / sum_gc_bc)


def analyze_team_process(filename_lst, res):
    '''
    分析阵容进程
    :param  filename_lst    文件名列表
    :param  res             结果存放列表
    '''
    for filename in filename_lst:
        with open(filename, "r") as fd:
            for p_team in fd:
                p_team = eval(p_team)
                lst, s = [], None
                for defense_team, attack_team_data in p_team.items():
                    if not attack_team_data[1]:
                        break
                    else:
                        s = attack_team_data[1] if s is None else s & attack_team_data[1]
                        if not s:
                            break
                    gc, bc = attack_team_data[2], attack_team_data[3]
                    lst.append([defense_team, gc, bc])
                else:
                    if s and get_bad_comment_rate(lst) >= 0.25:
                        for ch in ["羊驼", "布丁", "望", "裁缝", "水吃", "yly", "充电宝", "环奈", "万圣忍", "初音", "水黑"]:
                            if ch in s:
                                res.append(lst)
                                break


def analyze_best_pjjc_team():
    '''
    分析p场最优阵容
    '''
    # 生成参数列表
    data_path_lst = list(filter(lambda x: x != os.path.join(
        data_path, "data.txt"), glob.glob(data_path + "/*.txt")))
    params_lst = [[] for _ in range(proc_pool_size)]
    for i in range(len(data_path_lst)):
        params_lst[i % proc_pool_size].append(data_path_lst[i])

    res, p_list = Manager().list(), []
    for i in range(proc_pool_size):
        p = Process(target=analyze_team_process, args=(params_lst[i], res))
        p_list.append(p)
    for p in p_list:
        p.start()
    for p in p_list:
        p.join()

    # 按差评排序从小到大
    res.sort(key=get_bad_comment_rate, reverse=True)

    for r in res:
        print("%s\t%s\t%s\t" % (r[0][0].ljust(19), r[1][0].ljust(19), r[2][0]))


if __name__ == "__main__":
    # 获取数据库所有数据
    pcr_team = get_pcr_team(start_time="2020-11-04")

    # 各角色出场率胜率图表
    get_ch_attend_and_win_chart(pcr_team)

    # 获取我的pjjc所有阵容
    get_mypjjc_team(pcr_team)

    # 分析p场最优阵容
    analyze_best_pjjc_team()
