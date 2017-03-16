# coding:utf-8
# game factory scraper
# env:python 3.6 + lxml
# license:MIT
# author:winxos
# since:2017-02-19

import urllib.request
import urllib.error
import itertools
from lxml import etree
import json
from multiprocessing import Pool
from time import clock
from functools import partial

POOLS_SIZE = 20
TRY_TIMES = 100
SINGLE_THREAD_DEBUG = False
# SINGLE_THREAD_DEBUG = True
CONFIG = None

try:
    with open('grab_config.json', 'r', encoding='utf8') as fg:
        CONFIG = json.load(fg)
        # print("[debug] config loaded.")
except IOError as e:
    print("[error] %s" % e)
    exit()


def get_content(url, charset):
    global TRY_TIMES
    try:
        fc = urllib.request.urlopen(url)
        TRY_TIMES = 100 # todo 用类进行封装
        return etree.HTML(fc.read().decode(charset))
    except UnicodeDecodeError as ude:
        print("[error] decode error %s" % url)
        print("[debug] info %s" % ude)
    except urllib.error.URLError or TimeoutError:  # 捕捉访问异常，一般为timeout，信息在e中
        # print("[retry %d] %s" % (TRY_TIMES, url))
        # print(traceback.format_exc())
        TRY_TIMES -= 1
        if TRY_TIMES > 0:
            return get_content(url, charset)
        return None


def get_items(selector, xpath):
    return selector.xpath(xpath)


def get_pages(rule_id):
    s = get_content(CONFIG["rules"][rule_id]["games_page_url"] + "1", CONFIG["rules"][rule_id]["charset"])
    if s is None:
        return
    page_max = int(get_items(s, CONFIG["rules"][rule_id]["games_page_max"])[0])
    return [CONFIG["rules"][rule_id]["games_page_url"] + str(i) for i in range(1, page_max + 1)]


def get_page_games(rule_id, url):
    s = get_content(url, CONFIG["rules"][rule_id]["charset"])
    if s is None:
        return []
    games_href = get_items(s, CONFIG["rules"][rule_id]["games_href"])
    return games_href


def get_game_info(rule_id, url):
    s = get_content(url, CONFIG["rules"][rule_id]["charset"])
    if s is None:
        return
    game_name = "".join(get_items(s, CONFIG["rules"][rule_id]["game_name"]))
    game_detail = "".join([x.strip() for x in get_items(s, CONFIG["rules"][rule_id]["game_detail"])])
    game_src = "".join(get_items(s, CONFIG["rules"][rule_id]["game_src"]))
    return game_name, game_detail, url, game_src


def save_txt(name, data, mode='a'):
    with open(name, mode, encoding='utf8') as f:
        f.write(data)


def download(rule_id):
    st = clock()
    pool = Pool(processes=int(CONFIG["rules"][rule_id]["pool_size"]))
    print("[debug] downloading game pages list.")
    page_urls = get_pages(rule_id)
    func = partial(get_page_games, rule_id)
    game_list = []
    pi = pool.imap(func, page_urls)  # iterator for progress
    for i in range(len(page_urls)):
        game_list.append(pi.next())
        if i % POOLS_SIZE == 0:
            print("[debug] downloaded pages [%d/%d]" % (i, len(page_urls)))
    game_list = list(itertools.chain(*game_list))
    print('[debug] downloaded %d game urls. used:%f s' %
          (len(game_list), clock() - st))
    print('[debug] downloading game details, waiting.')
    func = partial(get_game_info, 0)
    if not SINGLE_THREAD_DEBUG:
        games_info = []
        gi = pool.imap(func, game_list)
        for i in range(len(game_list)):
            games_info.append(gi.next())
            if i % POOLS_SIZE == 0:
                print("[debug] downloading progress %.2f%%" %
                      (i * 100 / len(game_list)))
    else:
        games_info = []
        for gl in game_list[:10]:
            games_info.append(func(gl))
    print('[debug] downloaded %d game details. total used:%f s' %
          (len(games_info), clock() - st))
    for gi in games_info:
        save_txt(str(rule_id) + ".txt", '$'.join(map(str, gi)) + "\n")


'''
usage:
download(index of grab_config_game_lib)
'''
if __name__ == '__main__':
    download(0)
