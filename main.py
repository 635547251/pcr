# coding:utf-8
import glob
import json
import os
from collections import defaultdict
from multiprocessing import Manager, Process

from .config import data_path, proc_pool_size, start_time
from .db import get_pcr_team

with open("pcr/conf/ch.json", "r", encoding="utf-8") as f:
    d = json.load(f)
    main_tank = d["main_tank"]
    other_list = d["other_list"]
    all_ch_num = len(d["pos2ch_dic"])


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


def get_all_team(pcr_team: list[tuple[str]]):
    '''
    获取我的所有pjjc阵容记录
    '''
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
    return all_team


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

    all_team = get_all_team(pcr_team)
    filename = os.path.join(data_path, "data.txt")
    with open(filename, "w") as f:
        backtrace(3, list(all_team.keys()), f)

    # 分块切割文件
    file_end = os.path.getsize(filename)
    with open(filename, "rb") as f:
        for index, (chunk_start, size) in enumerate(chunkify(filename, file_end)):
            f.seek(chunk_start)
            lines = f.read(size).splitlines()
            with open(os.path.join(data_path, "data" + str(index) + ".txt"), "w") as f:
                for line in lines:
                    print(line.decode("utf-8"), file=f)


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
        with open(filename, "r") as f:
            for p_team in f:
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
                    if s:
                        res.append(lst)


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

    with open("pcr/res.txt", "w") as f:
        for r in res:
            print(r, file=f)
            # print("%s\t%s\t%s\t" % (r[0][0].ljust(19), r[1][0].ljust(19), r[2][0]))


if __name__ == "__main__":
    # 获取数据库所有数据
    pcr_team = get_pcr_team(start_time=start_time)

    # 获取我的pjjc所有阵容
    get_mypjjc_team(pcr_team)

    # 分析p场最优阵容
    analyze_best_pjjc_team()
