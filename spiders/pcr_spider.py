# coding:utf-8
import contextlib
import logging
import re
import time
from threading import Thread

import pymysql
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
# from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from ..config import (DB_DATABASE, DB_HOSTNAME, DB_PASSWORD, DB_USERNAME,
                      ch_blacklist, common_wait_time, get_team_page,
                      pos2ch_dic)
from .logutil import init_logging


@contextlib.contextmanager
def get_connection():
    conn = pymysql.connect(host=DB_HOSTNAME,
                           user=DB_USERNAME,
                           password=DB_PASSWORD,
                           database=DB_DATABASE,
                           charset="utf8")
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def insert_team(params):
    conn = get_connection()
    with get_connection() as conn:
        with conn.cursor() as cursor:
            insert_sql = '''
                    insert ignore into
                        T_TEAM (ATTACK_TEAM, DEFENSE_TEAM)
                    values
                        ("%s", "%s")
                '''
            try:
                for param in params:
                    cursor.execute(insert_sql % param)
                conn.commit()
                logging.info("插入表T_TEAM完成")
            except Exception as e:
                logging.error(e)
                # conn.rollback()


def pos2ch(s):
    return pos2ch_dic.get(re.match(r"(.*?)background-position:(.*?);(.*?)", s).group(2).strip())


class PcrSpiders(Thread):
    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        options = webdriver.chrome.options.Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        # driver.implicitly_wait(5)
        '''隐式等待和显示等待都存在时，超时时间取二者中较大的'''
        driver.get(self.url)
        time.sleep(common_wait_time)

        try:
            # 下拉菜单
            menu = WebDriverWait(driver, 10).until(
                lambda driver: driver.find_elements(By.CLASS_NAME, "ant-collapse-item"))
            logging.info("寻找下拉菜单成功")
            # 搜素按钮
            search = WebDriverWait(driver, 10).until(
                lambda driver: driver.find_element(By.CLASS_NAME, "battle_search_button"))
            logging.info("寻找搜索按钮成功")
            time.sleep(common_wait_time)
            # 切换至国服
            driver.find_element_by_xpath(
                "//div[@class='body_margin_content'][1]/div/label[2]").click()
            logging.info("切换至国服")
            time.sleep(common_wait_time)
            for m in menu:
                # 展开下拉菜单
                m.click()
                time.sleep(common_wait_time)
                # 人物列表
                character_list = m.find_elements_by_xpath("./div[2]/div/div")
                for chara in character_list:
                    # TODO 循环后显示'NoneType' object has no attribute 'group'
                    # 获取人物
                    ch = pos2ch(chara.get_attribute("style"))
                    # 排除角色
                    if ch in ch_blacklist:
                        continue
                    logging.info("获取角色%s" % ch)
                    # 搜索阵容
                    chara.click()
                    time.sleep(0.5)
                    search.click()
                    while True:
                        _search = driver.find_element_by_class_name(
                            "battle_search_button")
                        if _search.get_attribute("ant-click-animating-without-extra-node") == "false":
                            break
                        time.sleep(0.5)
                    time.sleep(common_wait_time)

                    # 获取4页防守阵容
                    team_list, next_but = [], None
                    for i in range(get_team_page):
                        # 每页结果阵容
                        res_list = driver.find_elements_by_class_name(
                            "battle_search_single_result_ctn")
                        if next_but is None:
                            next_but = driver.find_element_by_xpath(
                                "//div[@class='ant-btn-group ant-btn-group-sm']/button[2]")
                        for res in res_list:
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
                            if attack_team and defense_team and ch in defense_team:
                                team_list.append(
                                    (attack_team[:-1], defense_team[:-1]))
                                logging.info("进攻方:%s 防守方:%s" % (
                                    attack_team[:-1], defense_team[:-1]))
                        if i < get_team_page - 1:
                            next_but.click()
                            logging.info("%s阵容点击下一页" % ch)
                            while True:
                                _next_but = driver.find_element_by_xpath(
                                    "//div[@class='ant-btn-group ant-btn-group-sm']/button[2]")
                                if _next_but.get_attribute("ant-click-animating-without-extra-node") == "false":
                                    break
                                time.sleep(0.5)
                            time.sleep(common_wait_time)
                    # 入库
                    insert_team(team_list)
                    # 移出所选角色
                    ele = driver.find_element_by_xpath(
                        "//div[@class='battle_search_select'][1]/div[2]")
                    ActionChains(driver).move_to_element(
                        ele).click(ele).perform()
                    time.sleep(common_wait_time)
        except TimeoutException:
            logging.error("网络超时")
            raise
        finally:
            driver.quit()


def pcr_spider(log_q, url, headers):
    init_logging(log_q)

    t = PcrSpiders(url)
    t.start()
    t.join()
