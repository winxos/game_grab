# coding:utf-8
'''
game factory scraper
env:python 3.5
license:MIT
author:winxos
since:2017-02-19
'''
import urllib.request
import itertools
from lxml import etree
import json
from multiprocessing import Pool, Manager
from time import clock
import traceback
from functools import partial

POOLS_SIZE = 20
try_times = 3

with open('grab_config.json', 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)


def get_content(url, xpath, charset):
    global try_times
    try:
        f = urllib.request.urlopen(url)
        c = etree.HTML(f.read().decode(charset))
        try_times = 3
        return c.xpath(xpath)
    except Exception as e:  # 捕捉访问异常，一般为timeout，信息在e中
        print("[err] %s" % url)
        print(traceback.format_exc())
        try_times -= 1
        if try_times > 0:
            return get_content(url, xpath, charset)
        return None


def get_pages(RULE_ID):
    page_max = int(get_content(CONFIG["rules"][RULE_ID]["games_page_url"] + "1",
                               CONFIG["rules"][RULE_ID]["games_page_max"],
                               CONFIG["rules"][RULE_ID]["charset"])[0])
    return [CONFIG["rules"][RULE_ID]["games_page_url"] + str(i) for i in range(1, page_max + 1)]


def get_page_games(RULE_ID, url):
    games_href = get_content(url, CONFIG["rules"][RULE_ID]["games_href"],
                             CONFIG["rules"][RULE_ID]["charset"])
    return games_href


def get_game_info(RULE_ID, url):
    game_name = "".join(get_content(url, CONFIG["rules"][RULE_ID]["game_name"],
                                    CONFIG["rules"][RULE_ID]["charset"]))
    game_detail = "".join([x.strip() for x in
                           get_content(url,
                                       CONFIG["rules"][RULE_ID]["game_detail"],
                                       CONFIG["rules"][RULE_ID]["charset"])])
    game_src = "".join(get_content(url, CONFIG["rules"][RULE_ID]["game_src"],
                                   CONFIG["rules"][RULE_ID]["charset"]))
    return (game_name, game_detail, url, game_src)


def save_txt(name, data, mode='a'):
    with open(name, mode, encoding='utf8') as f:
        f.write(data)


def download(rule_id):
    st = clock()
    pool = Pool(processes=POOLS_SIZE)
    print("[debug] downloading game list.")
    func = partial(get_page_games, rule_id)
    game_list = pool.map(func, get_pages(rule_id))
    # pool.close()
    # pool.join()
    game_list = list(itertools.chain(*game_list))
    print('[debug] downloaded %d game urls. used:%f s' %
          (len(game_list), clock() - st))
    print('[debug] downloading game details, waiting.')
    func = partial(get_game_info, 0)
    games_info = pool.map(func, game_list)
    pool.close()
    pool.join()
    for gi in games_info:
        save_txt(str(rule_id) + ".txt", str(gi) + "\n")


'''
usage:
download(index of gamelib)
'''
if __name__ == '__main__':
    download(0)
