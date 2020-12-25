# coding:utf-8
import json
import logging
import re
import time
from threading import Thread

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
# from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from ..config import common_wait_time, start_time
from ..db import get_pcr_team, insert_team
from ..main import get_ch_attend_and_win
from .logutil import init_logging

with open("pcr/conf/ch.json", "r", encoding="utf-8") as f:
    d = json.load(f)
    ch_whitelist = d["ch_whitelist"]
    pos2ch_dic, pos2ch_6x_dic = d["pos2ch_dic"], d["pos2ch_6x_dic"]
    main_tank, other_list = d["main_tank"], d["other_list"]
    ch2index = {v: index for index, v in enumerate(pos2ch_dic.values())}


def pos2ch(s: str):
    '''
    坐标转人物
    :param  s   坐标
    :reutrn ch  人物
    '''
    r = re.match(
        r'.*?url\("(.*?)\.png\?.*?"\);.*?background-position:(.*?);.*?', s)
    url, pos = r.group(1).split("/")[-1], r.group(2)
    ret = pos2ch_dic.get(pos.strip()) if url == "charas" else pos2ch_6x_dic.get(
        pos.strip()) if url == "charas6x" else None
    logging.info("转换角色, url: %s pos: %s -> %s", url, pos, ret)
    return ret


class PcrSpiders(Thread):
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.driver = None  # 浏览器
        self.search = None  # 搜索按钮
        self.character_list = []  # 人物列表对象

    def crawl_ch(self, ch_lst: list[str]):
        for ch in ch_lst:
            chara = [self.character_list[ch2index[ch]] for ch in ch.split("|")]
            logging.info("获取角色%s" % ch)
            # 搜索阵容
            for i in range(len(chara)):
                ActionChains(self.driver).move_to_element(
                    chara[i]).click(chara[i]).perform()
                time.sleep(0.5)
            time.sleep(common_wait_time)
            ActionChains(self.driver).move_to_element(
                self.search).click(self.search).perform()
            time.sleep(common_wait_time)
            while True:
                _search = self.driver.find_element_by_class_name(
                    "battle_search_button")
                if _search.get_attribute("ant-click-animating-without-extra-node") == "false":
                    break
                time.sleep(common_wait_time)
            time.sleep(common_wait_time)

            # 获取get_team_page页防守阵容
            res_list, next_but = None, None
            while True:
                # 每页结果阵容
                while True:
                    if res_list is None or res_list != self.driver.find_elements_by_class_name(
                            "battle_search_single_result_ctn"):
                        res_list = self.driver.find_elements_by_class_name(
                            "battle_search_single_result_ctn")
                        break
                    else:
                        time.sleep(common_wait_time)
                if next_but is None:
                    next_but = WebDriverWait(self.driver, 10).until(
                        lambda driver: driver.find_element(By.XPATH, "//div[@class='ant-btn-group ant-btn-group-sm']/button[2]"))
                team_list, i = [], 0  # 计算列表数，好差评全为0时退出
                for res in res_list:
                    # 获取好评差评数
                    good_comment = res.find_element_by_xpath(
                        "./div[@class='battle_search_single_meta']/div[1]/button[1]/span").text.strip()
                    bad_comment = res.find_element_by_xpath(
                        "./div[@class='battle_search_single_meta']/div[1]/button[2]/span").text.strip()
                    if good_comment == bad_comment == "0" or good_comment == "" or bad_comment == "":
                        i += 1
                        continue
                    timestamp = res.find_element_by_xpath(
                        "./div[@class='battle_search_single_meta']/div[2]").text.strip()
                    # 每个结果阵容
                    defense_team, attack_team = "", ""
                    team = res.find_elements_by_xpath(
                        "./div[1]/div/div[2]/div/div[1]")
                    for j in range(len(team)):
                        c = pos2ch(team[j].get_attribute("style"))
                        if c is None:
                            defense_team = attack_team = ""
                            break
                        if j <= 4:
                            attack_team += c + "|"
                        else:
                            defense_team += c + "|"
                    if attack_team and defense_team:
                        team_list.append(
                            {
                                "ATTACK_TEAM": attack_team[:-1],
                                "DEFENSE_TEAM": defense_team[:-1],
                                "GOOD_COMMENT": int(good_comment),
                                "BAD_COMMENT": int(bad_comment),
                                "CREATE_TIMESTAMP": timestamp
                            }
                        )
                        logging.info("进攻方:%s 防守方:%s 好评:%s 差评:%s" % (
                            attack_team[:-1], defense_team[:-1], good_comment, bad_comment))
                if not team_list or i == len(res_list):
                    break
                # 入库
                insert_team(team_list)
                # 判断下一页是否能点击
                is_next = self.driver.find_element_by_xpath(
                    "//div[@class='ant-btn-group ant-btn-group-sm']/button[2]").is_enabled()
                if is_next:
                    ActionChains(self.driver).move_to_element(
                        next_but).click(next_but).perform()
                    logging.info("%s阵容点击下一页" % ch)
                    time.sleep(common_wait_time)
                    # 判断弹窗
                    win = self.driver.find_elements_by_xpath(
                        "//div[@class='ant-modal-content']")
                    if win:
                        b = self.driver.find_element_by_xpath(
                            "//div[@class='ant-modal-content']/div/div/div[2]/button")
                        ActionChains(self.driver).move_to_element(
                            b).click(b).perform()
                        break
                    while True:
                        _next_but = self.driver.find_element_by_xpath(
                            "//div[@class='ant-btn-group ant-btn-group-sm']/button[2]")
                        if _next_but.get_attribute("ant-click-animating-without-extra-node") == "false":
                            break
                        time.sleep(common_wait_time)
                    time.sleep(common_wait_time)
                else:
                    time.sleep(common_wait_time)
                    break
            # 移出所选角色
            ele = self.driver.find_elements_by_xpath(
                "//div[@class='battle_search_select'][1]/div")
            for i in range(1, len(chara) + 1):
                ActionChains(self.driver).move_to_element(
                    ele[i]).click(ele[i]).perform()
                time.sleep(0.5)
            self.driver.execute_script(
                "var q=document.documentElement.scrollTop=0")
            time.sleep(common_wait_time)

    def run(self):
        options = webdriver.chrome.options.Options()
        options.add_argument("--headless")
        options.add_argument("disable-infobars")  # 浏览器不显示受自动测试软件控制
        options.add_argument("--disable-gpu")  # 谷歌文档提到需要加上这个属性来规避bug
        options.add_argument("window-size=1920x3000")  # 指定浏览器分辨率
        self.driver = webdriver.Chrome(options=options)
        # driver.implicitly_wait(5)
        '''隐式等待和显示等待都存在时，超时时间取二者中较大的'''
        self.driver.get(self.url)
        time.sleep(common_wait_time)

        try:
            # 下拉菜单
            menu = WebDriverWait(self.driver, 10).until(
                lambda driver: driver.find_elements(By.CLASS_NAME, "ant-collapse-item"))
            logging.info("寻找下拉菜单成功")
            time.sleep(common_wait_time)
            # 搜素按钮
            self.search = WebDriverWait(self.driver, 10).until(
                lambda driver: driver.find_element(By.CLASS_NAME, "battle_search_button"))
            logging.info("寻找搜索按钮成功")
            time.sleep(common_wait_time)
            # 切换至国服
            self.driver.find_element_by_xpath(
                "//div[@class='body_margin_content'][1]/div/label[2]").click()
            logging.info("切换至国服")
            time.sleep(common_wait_time)

            for m in menu:
                # 展开下拉菜单
                ActionChains(self.driver).move_to_element(
                    m).click(m).perform()
                time.sleep(common_wait_time)
                # 人物列表
                self.character_list += m.find_elements_by_xpath(
                    "./div[2]/div[1]/div")

            # 爬取各个人物
            self.crawl_ch(ch_whitelist)

            # 存储数据
            ch_attend_and_win = get_ch_attend_and_win(
                get_pcr_team(start_time=start_time))
            ch_2_combo, my_chlist = [], set(main_tank + other_list)
            for k, v in ch_attend_and_win["2"][0].items():
                if v >= 5:
                    for ch in k.split("|"):
                        if ch not in my_chlist:
                            break
                    else:
                        ch_2_combo.append(k)
            with open("pcr/conf/combo.json", "w") as f:
                json.dump(ch_2_combo, f, ensure_ascii=False, indent=2)

            # 爬取组合
            with open("pcr/conf/combo.json", "r") as f:
                ch_2_combo = json.load(f)
            self.crawl_ch(ch_2_combo)
        except TimeoutException:
            logging.error("网络超时")
            raise
        except Exception as e:
            logging.error(e)
            raise
        finally:
            self.driver.quit()


def pcr_spider(log_q, url, headers):
    init_logging(log_q)

    t = PcrSpiders(url)
    t.start()
    t.join()
