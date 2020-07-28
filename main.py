from .spiders.pcr_spider import get_connection


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


def get_ch_appearance(pcr_team):
    '''
    统计各个人物出场次数、出处率
    '''
    team = set()
    for attack_team, defense_team in pcr_team:
        team.add(attack_team)
        team.add(defense_team)
    team_len = len(team)
    ch_appearance_time, ch_appearance_rate = {}, {}
    for t in team:
        for ch in t.split("|"):
            ch_appearance_time[ch] = ch_appearance_time.get(ch, 0) + 1
    for k, v in ch_appearance_time.items():
        ch_appearance_rate[k] = "{:.2%}".format(v / team_len)
    ch_appearance_time = list(dict(
        sorted(ch_appearance_time.items(), key=lambda x: x[1], reverse=True)).items())
    ch_appearance_rate = list(dict(
        sorted(ch_appearance_rate.items(), key=lambda x: float(x[1][:-1]), reverse=True)).items())
    return ch_appearance_time, ch_appearance_rate


def get_ch_win(pcr_team):
    '''
    统计各个人物胜场次数、胜率
    '''
    ch_win_time, ch_all_time, ch_win_rate = {}, {}, {}
    for attack_team, defense_team in pcr_team:
        for ch in attack_team.split("|"):
            ch_win_time[ch] = ch_win_time.get(ch, 0) + 1
            ch_all_time[ch] = ch_all_time.get(ch, 0) + 1
        for ch in defense_team.split("|"):
            ch_all_time[ch] = ch_all_time.get(ch, 0) + 1
    for k, v in ch_win_time.items():
        ch_win_rate[k] = "{:.2%}".format(v / ch_all_time[k])
    ch_win_time = list(dict(
        sorted(ch_win_time.items(), key=lambda x: x[1], reverse=True)).items())
    ch_win_rate = list(dict(
        sorted(ch_win_rate.items(), key=lambda x: float(x[1][:-1]), reverse=True)).items())
    return ch_win_time, ch_win_rate


def backtrace(n, t_list, ch_combo_time, i=0, res=[]):
    if len(res) == n:
        ch_combo_time["|".join(res)] = ch_combo_time.get(
            "|".join(res), 0) + 1
        return
    else:
        for j in range(i, len(t_list)):
            backtrace(n, t_list, ch_combo_time, j + 1, res + [t_list[j]])


def get_ch_combo_appearance(pcr_team, n=2):
    '''
    统计n人组合出场次数、出场率
    '''
    team, ch_combo_appearance_time, ch_combo_appearance_rate = set(), {}, {}
    for attack_team, defense_team in pcr_team:
        team.add(attack_team)
        team.add(defense_team)
    team_len = len(team)
    for t in team:
        backtrace(n, t.split("|"), ch_combo_appearance_time)
    for k, v in ch_combo_appearance_time.items():
        ch_combo_appearance_rate[k] = "{:.2%}".format(v / team_len)
    ch_combo_appearance_time = list(dict(
        sorted(ch_combo_appearance_time.items(), key=lambda x: x[1], reverse=True)).items())
    ch_combo_appearance_rate = list(dict(
        sorted(ch_combo_appearance_rate.items(), key=lambda x: float(x[1][:-1]), reverse=True)).items())
    return ch_combo_appearance_time, ch_combo_appearance_rate


def get_ch_combo_win(pcr_team, n=2):
    '''
    统计n人组合胜场次数、胜率
    '''
    ch_combo_win_time, ch_combo_lose_time, ch_combo_win_rate = {}, {}, {}
    for attack_team, defense_team in pcr_team:
        backtrace(n, attack_team.split("|"), ch_combo_win_time)
        backtrace(n, defense_team.split("|"), ch_combo_lose_time)
    for k, v in ch_combo_win_time.items():
        ch_combo_win_rate[k] = "{:.2%}".format(v / (v + ch_combo_lose_time.get(k, 0)))
    ch_combo_win_time = list(dict(
        sorted(ch_combo_win_time.items(), key=lambda x: x[1], reverse=True)).items())
    ch_combo_win_rate = list(dict(
        sorted(ch_combo_win_rate.items(), key=lambda x: float(x[1][:-1]), reverse=True)).items())
    return ch_combo_win_time, ch_combo_win_rate


if __name__ == "__main__":
    pcr_team = get_pcr_team()
    # 出场次数 出场率
    ch_appearance_time, ch_appearance_rate = get_ch_appearance(pcr_team)
    # 胜场次数 胜场率
    ch_win_time, ch_win_rate = get_ch_win(pcr_team)

    # 2人组合
    ch_2_combo_time, ch_2_combo_rate = get_ch_combo_appearance(pcr_team, 2)
    ch_2_combo_win_time, ch_2_combo_win_rate = get_ch_combo_win(pcr_team, 2)
    # 3人组合
    ch_3_combo_time, ch_3_combo_rate = get_ch_combo_appearance(pcr_team, 3)
    ch_3_combo_win_time, ch_3_combo_win_rate = get_ch_combo_win(pcr_team, 3)
    # 4人组合
    ch_4_combo_time, ch_4_combo_rate = get_ch_combo_appearance(pcr_team, 4)
    ch_4_combo_win_time, ch_4_combo_win_rate = get_ch_combo_win(pcr_team, 4)
