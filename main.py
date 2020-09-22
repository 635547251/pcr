import json
import pickle
from collections import defaultdict
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import ticker

from .config import ranking
from .db import get_pcr_team

with open("pcr/conf/ch.json", "r") as f:
    d = json.load(f)
    main_tank = d["main_tank"]
    other_list = d["other_list"]

# 这两行代码解决 plt 中文显示的问题
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


def get_ch_attend_and_win(pcr_team: List[Tuple[str]]) -> Dict:
    '''
    统计1-4人组合出场率, 胜率
    :param  pcr_team            数据库查询结果
    :return ch_attend_and_time  各组合的xy轴字典
    '''
    def backtrace(t_list, output_1, output_2, output_3, output_4, i=0, res=[]):
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
    # 胜利次数 战斗总数
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


def get_ch_attend_and_win_chart(pcr_team: List[Tuple[str]]):
    '''
    获取各角色出场率胜率图表
    :param  pcr_team    数据库查询结果
    '''
    def get_axis(ch_attend_time: Dict, ch_win_time: Dict, ch_lose_time: Dict) -> Tuple[List]:
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
        y_axis = [ch[0] for ch in ch_attend_rate]  # y轴 角色
        x_axis1 = [ch[1] for ch in ch_attend_rate]  # x轴1 出场率
        x_axis2 = [round(ch_win_time[ch] / (ch_win_time[ch] + ch_lose_time[ch]), 4)
                   for ch in y_axis][::-1]  # x轴2 胜率

        return y_axis, x_axis1, x_axis2

    def generate_chart(y_axis, x_axis1, x_axis2, title, height=0.8, n=2):
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
        # plt.axes([0.14, 0.05, 0.77, 0.2])
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
    generate_chart(get_axis(*ch_attend_and_win["1"]), title="各个角色")
    fig.legend(loc="upper right")  # 标签
    # 2人组合
    plt.subplot(222)
    generate_chart(get_axis(*ch_attend_and_win["2"]), title="2人组合")
    # 3人组合
    plt.subplot(223)
    generate_chart(get_axis(*ch_attend_and_win["3"]), title="3人组合")
    # 4人组合
    plt.subplot(224)
    generate_chart(get_axis(*ch_attend_and_win["4"]), title="4人组合")

    plt.show()


def get_mypjjc_team(pcr_team: List[Tuple[str]]) -> List[Dict]:
    '''
    获取我的pjjc所有阵容
    :param  pcr_team    数据库查询结果
    :return data        我的所有阵容
    '''
    def backtrace(n, t_list, output, i=0, res=[]):
        if len(res) == n:
            output.append({r: all_team[r] for r in res})
            return
        else:
            for j in range(i, len(t_list)):
                if res:
                    # 去除重复角色
                    _res = set("|".join(res).split("|"))
                    for ch in t_list[j].split("|"):
                        if ch in _res:
                            break
                    else:
                        backtrace(n, t_list, output, j + 1, res + [t_list[j]])
                else:
                    backtrace(n, t_list, output, j + 1, res + [t_list[j]])

    # 获取我的所有pjjc阵容记录
    _main_tank, my_chlist = set(main_tank), set(main_tank + other_list)
    all_team = defaultdict(list)
    for attack_team, defense_team, good_comment, bad_comment in pcr_team:
        d_sp = defense_team.split("|")
        for ch in d_sp:
            if ch not in my_chlist or d_sp[-1] not in _main_tank:
                break
        else:
            all_team[defense_team].append(
                [attack_team, good_comment, bad_comment])

    data = []
    # TODO 回溯算法优化 大数据存储
    backtrace(3, list(all_team.keys()), data)
    with open("pcr/conf/data.txt", "wb") as fd:
        pickle.dump(data, fd, protocol=pickle.HIGHEST_PROTOCOL)


def analyze_best_pjjc_team():
    '''
    分析p场最优阵容
    '''
    with open("pcr/conf/data.txt", "rb") as fd:
        mypjjc_team = pickle.load(fd)

    res = []
    for p_team in mypjjc_team:
        lst = []
        for defense_team, attack_team in p_team.items():
            good_comment = bad_comment = 0
            for att, gc, bc in attack_team:
                if "yly" not in att:
                    break
                good_comment += gc
                bad_comment += bc
            else:
                lst.append([defense_team, gc, bc])
        if len(lst) == 3:
            res.append(lst)
    # 按差评排序从小到大
    res.sort(
        key=lambda x: (x[0][2] + x[1][2] + x[2][2]) /
        (x[0][2] + x[1][2] + x[2][2] + x[0][1] + x[1][1] + x[2][1]),
        reverse=True)

    # 打印前5%结果
    for r in res[:len(res)//20]:
        print("%s\t%s\t%s\t" % (r[0][0].ljust(18), r[1][0].ljust(18), r[2][0]))


if __name__ == "__main__":
    # 获取数据库所有数据
    pcr_team = get_pcr_team(start_time="2020-09-14")

    # 各角色出场率胜率图表
    get_ch_attend_and_win_chart(pcr_team)

    # 获取我的pjjc所有阵容
    get_mypjjc_team(pcr_team)

    # 分析p场最优阵容
    analyze_best_pjjc_team()
