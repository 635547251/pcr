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

from ..common import get_connection
from ..config import common_wait_time
from .logutil import init_logging

with open("pcr/conf/ch.json", "r") as f:
    d = json.load(f)
    ch_whitelist = d["ch_whitelist"]
    pos2ch_dic, pos2ch_6x_dic = d["pos2ch_dic"], d["pos2ch_6x_dic"]


def insert_team(params):
    conn = get_connection()
    with get_connection() as conn:
        with conn.cursor() as cursor:
            insert_sql = '''
                    insert into
                        T_TEAM (ATTACK_TEAM, DEFENSE_TEAM, GOOD_COMMENT, BAD_COMMENT,
                            CREATE_TIMESTAMP, UPDATE_TIMESTAMP)
                    values
                        ("{ATTACK_TEAM}", "{DEFENSE_TEAM}", "{GOOD_COMMENT}", "{BAD_COMMENT}",
                        "{CREATE_TIMESTAMP}", current_timestamp())
                    on duplicate key update
                        GOOD_COMMENT = "{GOOD_COMMENT}",
                        BAD_COMMENT = "{BAD_COMMENT}",
                        UPDATE_TIMESTAMP = current_timestamp()
                '''
            try:
                for param in params:
                    cursor.execute(insert_sql.format(**param))
                conn.commit()
                logging.info("插入表T_TEAM完成")
            except Exception as e:
                logging.error(e)
                # conn.rollback()
                raise


def pos2ch(s):
    r = re.match(
        r'.*?url\("(.*?)\.png\?.*?"\);.*?background-position:(.*?);.*?', s)
    url, pos = r.group(1).split("/")[-1], r.group(2)
    return pos2ch_dic.get(pos.strip()) if url == "charas" else pos2ch_6x_dic.get(pos.strip()) if url == "charas6x" else None


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
                ActionChains(driver).move_to_element(
                    m).click(m).perform()
                time.sleep(common_wait_time)
                # 人物列表
                character_list = m.find_elements_by_xpath(
                    "./div[2]/div[1]/div")
                for chara in character_list:
                    # TODO 循环后显示'NoneType' object has no attribute 'group'
                    # 获取人物
                    try:
                        ch = pos2ch(chara.get_attribute("style"))
                    except AttributeError as e:
                        logging.error(e)
                        break
                    # 排除角色
                    if ch not in ch_whitelist:
                        continue
                    logging.info("获取角色%s" % ch)
                    # 搜索阵容
                    ActionChains(driver).move_to_element(
                        chara).click(chara).perform()
                    time.sleep(common_wait_time)
                    ActionChains(driver).move_to_element(
                        search).click(search).perform()
                    time.sleep(common_wait_time)
                    while True:
                        _search = driver.find_element_by_class_name(
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
                            if res_list is None or res_list != driver.find_elements_by_class_name(
                                    "battle_search_single_result_ctn"):
                                res_list = driver.find_elements_by_class_name(
                                    "battle_search_single_result_ctn")
                                break
                            else:
                                time.sleep(common_wait_time)
                        if next_but is None:
                            next_but = WebDriverWait(driver, 10).until(
                                lambda driver: driver.find_element(By.XPATH, "//div[@class='ant-btn-group ant-btn-group-sm']/button[2]"))
                        team_list, i = [], 0  # 计算列表数，好差评全为0时退出
                        for res in res_list:
                            # 获取好评差评数
                            good_comment = res.find_element_by_xpath(
                                "./div[@class='battle_search_single_meta']/div[1]/button[1]/span").text.strip()
                            bad_comment = res.find_element_by_xpath(
                                "./div[@class='battle_search_single_meta']/div[1]/button[2]/span").text.strip()
                            if good_comment == bad_comment == "0" or good_comment == "" or bad_comment == "" or int(good_comment) + int(bad_comment) < 5:
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
                            if attack_team and defense_team and ch in defense_team:
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
                        is_next = driver.find_element_by_xpath(
                            "//div[@class='ant-btn-group ant-btn-group-sm']/button[2]").is_enabled()
                        if is_next:
                            ActionChains(driver).move_to_element(
                                next_but).click(next_but).perform()
                            logging.info("%s阵容点击下一页" % ch)
                            time.sleep(common_wait_time)
                            # 判断弹窗
                            win = driver.find_elements_by_xpath(
                                "//div[@class='ant-modal-content']")
                            if win:
                                b = driver.find_element_by_xpath(
                                    "//div[@class='ant-modal-content']/div/div/div[2]/button")
                                ActionChains(driver).move_to_element(
                                    b).click(b).perform()
                                break
                            while True:
                                _next_but = driver.find_element_by_xpath(
                                    "//div[@class='ant-btn-group ant-btn-group-sm']/button[2]")
                                if _next_but.get_attribute("ant-click-animating-without-extra-node") == "false":
                                    break
                                time.sleep(common_wait_time)
                            time.sleep(common_wait_time)
                        else:
                            time.sleep(common_wait_time)
                            break
                    # 移出所选角色
                    ele = driver.find_element_by_xpath(
                        "//div[@class='battle_search_select'][1]/div[2]")
                    ActionChains(driver).move_to_element(
                        ele).click(ele).perform()
                    time.sleep(common_wait_time)
        except TimeoutException:
            logging.error("网络超时")
            raise
        except Exception as e:
            logging.error(e)
            raise
        finally:
            driver.quit()


def pcr_spider(log_q, url, headers):
    init_logging(log_q)

    t = PcrSpiders(url)
    t.start()
    t.join()
