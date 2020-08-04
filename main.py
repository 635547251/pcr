import matplotlib.pyplot as plt
import numpy as np
from matplotlib import ticker

from .config import ranking
from .spiders.pcr_spider import get_connection

# 这两行代码解决 plt 中文显示的问题
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


def get_pcr_team():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            select_sql = '''
                    select ATTACK_TEAM, DEFENSE_TEAM from T_TEAM
                '''
            try:
                cursor.execute(select_sql)
                return cursor.fetchall()
            except Exception as e:
                print(e)
                raise


def get_ch_attend(pcr_team):
    '''
    统计各个人物出场率
    '''
    team = set()
    for attack_team, defense_team in pcr_team:
        team.add(attack_team)
        team.add(defense_team)
    team_len = len(team)
    ch_attend_time, ch_attend_rate = {}, {}
    for t in team:
        for ch in t.split("|"):
            ch_attend_time[ch] = ch_attend_time.get(ch, 0) + 1
    for k, v in ch_attend_time.items():
        ch_attend_rate[k] = round(v / team_len, 4)
    ch_attend_rate = dict(
        sorted(ch_attend_rate.items(), key=lambda x: x[1], reverse=True))

    return ch_attend_rate


def get_ch_win(pcr_team):
    '''
    统计各个人物胜率
    '''
    ch_win_time, ch_all_time, ch_win_rate = {}, {}, {}
    for attack_team, defense_team in pcr_team:
        for ch in attack_team.split("|"):
            ch_win_time[ch] = ch_win_time.get(ch, 0) + 1
            ch_all_time[ch] = ch_all_time.get(ch, 0) + 1
        for ch in defense_team.split("|"):
            ch_all_time[ch] = ch_all_time.get(ch, 0) + 1
    for k, v in ch_win_time.items():
        ch_win_rate[k] = round(v / ch_all_time[k], 4)
    ch_win_rate = dict(
        sorted(ch_win_rate.items(), key=lambda x: x[1], reverse=True))
    return ch_win_rate


def backtrace(n, t_list, ch_combo_time, i=0, res=[]):
    if len(res) == n:
        ch_combo_time["|".join(res)] = ch_combo_time.get(
            "|".join(res), 0) + 1
        return
    else:
        for j in range(i, len(t_list)):
            backtrace(n, t_list, ch_combo_time, j + 1, res + [t_list[j]])


def get_ch_combo_attend(pcr_team, n=2):
    '''
    统计n人组合出场次数、出场率
    '''
    team, ch_combo_attend_time, ch_combo_attend_rate = set(), {}, {}
    for attack_team, defense_team in pcr_team:
        team.add(attack_team)
        team.add(defense_team)
    team_len = len(team)
    for t in team:
        backtrace(n, t.split("|"), ch_combo_attend_time)
    for k, v in ch_combo_attend_time.items():
        ch_combo_attend_rate[k] = round(v / team_len, 4)
    ch_combo_attend_rate = dict(
        sorted(ch_combo_attend_rate.items(), key=lambda x: x[1], reverse=True))
    return ch_combo_attend_rate


def get_ch_combo_win(pcr_team, n=2):
    '''
    统计n人组合胜场次数、胜率
    '''
    ch_combo_win_time, ch_combo_lose_time, ch_combo_win_rate = {}, {}, {}
    for attack_team, defense_team in pcr_team:
        backtrace(n, attack_team.split("|"), ch_combo_win_time)
        backtrace(n, defense_team.split("|"), ch_combo_lose_time)
    for k, v in ch_combo_win_time.items():
        ch_combo_win_rate[k] = round(v / (v + ch_combo_lose_time.get(k, 0)), 4)
    ch_combo_win_rate = dict(
        sorted(ch_combo_win_rate.items(), key=lambda x: x[1], reverse=True))
    return ch_combo_win_rate


def get_ch_attend_and_win_chart(ch_attend_rate, ch_win_rate, title, height=0.8, n=2):
    '''
    获取角色出场率和胜率图表
    '''
    def to_percent(temp, position):
        return "%1.0f" % (100 * temp) + "%"

    y_axis = list(ch_attend_rate)[:ranking][::-1]  # y轴 角色
    x_axis1 = list(ch_attend_rate.values())[:ranking][::-1]  # x轴1 出场率
    x_axis2 = [ch_win_rate.get(ch, 0) for ch in y_axis][:ranking]  # x轴2 胜率

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


def main(pcr_team):
    fig = plt.figure(figsize=(16, 8))
    fig.canvas.set_window_title("pcr国服各角色出场率TOP%s及胜率" % ranking)  # 窗口名
    fig.subplots_adjust(left=0.1, right=0.97, top=0.95,
                        bottom=0.05, wspace=0.3)  # 子图间距
    # fig.tight_layout()  # 自动调整标签

    # 各角色
    plt.subplot(221)
    ch_attend_rate = get_ch_attend(pcr_team)
    ch_win_rate = get_ch_win(pcr_team)
    get_ch_attend_and_win_chart(
        ch_attend_rate, ch_win_rate, "各个角色")
    fig.legend(loc="upper right")  # 标签

    # 2人组合
    plt.subplot(222)
    ch_2_combo_rate = get_ch_combo_attend(pcr_team, 2)
    ch_2_combo_win_rate = get_ch_combo_win(pcr_team, 2)
    get_ch_attend_and_win_chart(
        ch_2_combo_rate, ch_2_combo_win_rate, "2人组合")
    # 3人组合
    plt.subplot(223)
    ch_3_combo_rate = get_ch_combo_attend(pcr_team, 3)
    ch_3_combo_win_rate = get_ch_combo_win(pcr_team, 3)
    get_ch_attend_and_win_chart(
        ch_3_combo_rate, ch_3_combo_win_rate, "3人组合")
    # 4人组合
    plt.subplot(224)
    ch_4_combo_rate = get_ch_combo_attend(pcr_team, 4)
    ch_4_combo_win_rate = get_ch_combo_win(pcr_team, 4)
    get_ch_attend_and_win_chart(
        ch_4_combo_rate, ch_4_combo_win_rate, "4人组合")

    plt.show()


if __name__ == "__main__":
    main(get_pcr_team())
