# -*- coding: UTF-8 -*-
import time
import re
import difflib
import aiomysql
import argparse
import sys
from config import *
from bs4 import BeautifulSoup
from opnieuw import retry_async
from colorama import init, Fore, Style


@retry_async(retry_on_exceptions=except_tuple, max_calls_total=3, retry_window_after_first_call_in_seconds=60)
async def scan(url, sem):
    async with sem:
        try:
            global normal_count
            global error_count
            async with aiohttp.ClientSession() as session:
                async with session.get(url=url, allow_redirects=False, headers=headers, verify_ssl=False,
                                       timeout=15) as resp:
                    normal_count = normal_count + 1
                    text = await resp.text(errors='ignore')
                    status = resp.status
                    soup = BeautifulSoup(text, 'html.parser')
                    title = str(soup.find('title'))
                    title = title.strip('</title>')
                    title = title.replace('\t', '').replace('\n', '').replace('\r', '')
                    if '=' in title:
                        title = re.search('>.+</title>', text)
                        if title:
                            title = title.group()
                            title = title.strip('>').strip('</title')
                    if status in [200]:
                        for index in urls:
                            if index in url:
                                url2 = index
                        if re.search('/$', url2):
                            url2 = url2 + random_str + '/'
                        else:
                            url2 = url2 + '/' + random_str + '/'
                        if "404.css" in text or "404.js" in text or "404.html" in text or "404" in text or \
                                "not found" in text or 'error' in text or "找不到页面" in text:
                            print(Fore.GREEN+url+'  ---> 当前页面可能为响应码为200的404界面'+Style.RESET_ALL)
                            maybe_alive_list.add(url + "\t%d\t%s\n" % (status, title))
                        else:
                            async with session.get(url=url2, allow_redirects=False, headers=headers,
                                                   verify_ssl=False, timeout=15) as resp2:
                                status2 = resp2.status
                                text2 = await resp2.text(errors='ignore')
                                if status2 == 200:
                                    s = difflib.SequenceMatcher(isjunk=None, a=text, b=text2, autojunk=False)
                                    if s.ratio() < 0.9:
                                        print(Fore.GREEN+url+'  ---> 响应200可能存活'+Style.RESET_ALL)
                                        maybe_alive_list.add(url + "\t%d\t%s\n" % (status, title))
                                elif status2 == 404:
                                    print(Fore.GREEN+url+'  ---> 正常存活'+Style.RESET_ALL)
                                    status_200_list.add(url + "\t%d\t%s\n" % (status, title))
                                    for top in top_list:
                                        if top in url:
                                            alive_path = '/' + url.split(top)[1]
                                    await update_db(alive_path)
                    elif status == 403:
                        for index in urls:
                            if index in url:
                                url2 = index
                        if re.search('/$', url2):
                            url2 = url2 + random_str + '/'
                        else:
                            url2 = url2 + '/' + random_str + '/'
                        async with session.get(url=url2, allow_redirects=False, headers=headers, verify_ssl=False,
                                               timeout=15) as resp2:
                            if resp2.status == [200, 404]:
                                print(Fore.RED+url+'  ---> 403界面正常' + Style.RESET_ALL)
                                alive_403_30X_list.add(url + "\t%d\t%s\n" % (status, title))
                                if r_scan:
                                    if re.search('/$', url):        # 目录遍历
                                        url = str(url).strip('/')
                                    urls2.append(url)
                                    await append_url(url)
                            else:
                                print(url+'  --> 403界面异常,url应该不存在')
                    elif '30' in str(status):
                        for index in urls:
                            if index in url:
                                url2 = index
                        async with session.get(url=url, headers=headers, verify_ssl=False, timeout=15) as resp2:
                            async with session.get(url=url2, headers=headers, verify_ssl=False, timeout=15) as resp3:
                                text2 = await resp2.text(errors='ignore')
                                status2 = resp2.status
                                soup2 = BeautifulSoup(text2, 'html.parser')
                                title2 = str(soup2.find('title'))
                                title2 = title2.strip('</title>')
                                title2 = title2.replace('\t', '').replace('\n', '').replace('\r', '')
                                if '=' in title2:
                                    title2 = re.search('>.+</title>', text)
                                    if title2:
                                        title2 = title2.group()
                                        title2 = title2.strip('>').strip('</title')
                                if resp2.url == url + '/' and status2 == 404:
                                    url2 = url2 + '/' + random_str
                                    async with session.get(url=url2, headers=headers, allow_redirects=False, 
                                                           verify_ssl=False, timeout=15) as resp4:
                                        if resp4.status == 404:
                                            print(Fore.GREEN+url+'  ---> 此目录多半存在')
                                            maybe_alive_list.add(url + "\t%d\t%s\n" % (status2, title2))
                                            if r_scan:
                                                urls2.append(url)
                                                await append_url(url)      
                                if resp3.url != resp2.url and status2 == 200:
                                    if "404.css" in text2 or "404.js" in text2 or "404.html" in text2 or "404" in text2 or \
                                            "not found" in text2 or "找不到页面" in text2 or "error" in text2:
                                        print(Fore.GREEN+url+'  ---> 当前页面可能为响应码为30X的404界面' + str(resp2.url)+Style.RESET_ALL)
                                        maybe_alive_list.add(url + "\t%d\t%s\n" % (status, title2))
                                    else:
                                        async with session.get(url=url2, headers=headers,  verify_ssl=False,
                                                               timeout=15) as resp4:
                                            status4 = resp4.status
                                            text4 = await resp4.text(errors='ignore')
                                            if status4 == 200:
                                                s = difflib.SequenceMatcher(isjunk=None, a=text, b=text4,
                                                                            autojunk=False)
                                                if s.ratio() < 0.9:
                                                    print(Fore.GREEN+url+'  ---> 响应200可能存活'+Style.RESET_ALL)
                                                    maybe_alive_list.add(url + "\t%d\t%s\n" % (status, title2))
                                            elif status2 == 404:
                                                print(Fore.WHITE+url+'  ---> 正常存活'+Style.RESET_ALL)
                                                status_200_list.add(url + "\t%d\t%s\n" % (status, title2))
                                                for top in top_list:
                                                    if top in url:
                                                        alive_path = '/' + url.split(top)[1]
                                                await update_db(alive_path)
                                if status2 == 403:
                                    for index in urls:
                                        if index in url:
                                            url2 = index
                                    if re.search('/$', url2):
                                        url2 = url2 + random_str + '/'
                                    else:
                                        url2 = url2 + '/' + random_str + '/'
                                    async with session.get(url=url2, headers=headers,verify_ssl=False, timeout=15) as resp4:
                                        if resp4.status == [200, 404]:
                                            print(Fore.RED+url+'  ---> 403界面正常'+Style.RESET_ALL)
                                            alive_403_30X_list.add(url + "\t%d\t%s\n" % (status, title2))
                                            if r_scan:
                                                if re.search('/$', url):  # 目录遍历
                                                    url = str(url).strip('/')
                                                urls2.append(url)
                                                await append_url(url)
                                        else:
                                            print(url + '  --> 403界面异常,url应该不存在')
                                    if r_scan:
                                        if re.search('/$', str(resp2.url)):            # 目录遍历
                                            r_url = str(resp2.url).strip('/')
                                        urls2.append(r_url)
                                        await append_url(r_url)
                                else:
                                    other_list.add(url + "\t%d\t%s\n" % (status, title2))
                    elif status == 404:
                        print(str(url) + '  -------->  404')
                    else:
                        print(Fore.YELLOW+url+"  --> 其他没考虑到的情况"+Style.RESET_ALL)
                        other_list.add(url + "\t%d\t%s\n" % (status, title))
        except asyncio.TimeoutError:
            print(url + '\t' + "连接超时")
            error_count += 1
        except aiohttp.client.ClientOSError as e:
            print(url + '\t' + str(e))
            error_count += 1
        if dir_name != result:
            path1 = os.path.join(result, dir_name, 'a.txt')
            path2 = os.path.join(result, dir_name, 'b.txt')
            path3 = os.path.join(result, dir_name, 'c.txt')
            path4 = os.path.join(result, dir_name, 'other.txt')
        else:
            path1 = os.path.join(dir_name, 'a.txt')
            path2 = os.path.join(dir_name, 'b.txt')
            path3 = os.path.join(dir_name, 'c.txt')
            path4 = os.path.join(dir_name, 'd.txt')
        if len(status_200_list):
            f1 = open(path1, 'w+', encoding='utf-8')
            f1.writelines(status_200_list)
            f1.close()
        if len(alive_403_30X_list):
            f2 = open(path2, 'w+', encoding='utf-8')
            f2.writelines(alive_403_30X_list)
            f2.close()
        if len(maybe_alive_list):
            f3 = open(path3, 'w+', encoding='utf-8')
            f3.writelines(maybe_alive_list)
            f3.close()
        if len(other_list):
            f4 = open(path4, 'w+', encoding='utf-8')
            f4.writelines(other_list)
            f4.close()


async def append_url(add_url):
    for path in dir_list:
        scan_urls2.append(add_url+path)


async def conn_db(loop):
    async with aiomysql.create_pool(host='localhost',port=3306,user='root',password='密码',db='字典数据库名',loop=loop) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('select dir_name from test order by count desc')
                datas = await cursor.fetchall()
                datas_list = list(datas)
                for test in datas_list:
                    test123 = str(test).strip('(\'').strip('\',)')
                    dir_list.append(test123)
        pool.close()
        await pool.wait_closed()


async def update_db(alive_path):
    async with aiomysql.create_pool(host='localhost', port=3306, user='root', password='密码', db='字典数据库名',
                                    loop=loop) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("select count from test where dir_name = '%s'" % alive_path)
                old_count = await cursor.fetchone()
                old_count = str(old_count).strip('(\'').strip('\',)')
                new_count = int(old_count) + 1
                await cursor.execute("update test set count='%s' where dir_name = '%s'" % (new_count, alive_path))
        pool.close()
        await pool.wait_closed()


def parser_args():
    parser = argparse.ArgumentParser(usage='python3 dirsearch.py --target [urls file] [-o] [Storage path]')
    parser.add_argument('-t', '--target', dest='target', help='The path where the urls file is located', required=True)
    parser.add_argument('-o', '--output', dest='output', help='The location of the results', required=False, default=result)
    parser.add_argument('-r', '--recursive', dest='recursive', help='Recursive scan', action='store_true', required=False, default=False)
    if len(sys.argv) == 1:
        sys.argv.append('-h')
    args = parser.parse_args()
    return args


def main():
    with open(url_file, 'r') as fr:
        for line in fr.readlines():
            if line[0:4] != 'http':
                line = 'http://' + line
            line = line.strip('/')
            if line.strip() == '':
                continue
            urls.append(line.strip('/'))
    for url in urls:
        for path in dir_list:
            scan_urls.append(url + path)
    if dir_name != result:  # 如果路径 path 存在，返回 True；如果路径 path 不存在，返回 False。
        if not os.path.exists(result+'\\'+dir_name):
            os.mkdir(result+'\\'+dir_name)  # 创建目录
            print("结果放在result目录下的子目录：:", dir_name)
        else:
            print("该目录已存在，请更换目录名")


if __name__ == "__main__":
    start = time.time()
    argv = parser_args()
    url_file, dir_name, r_scan = argv.target, argv.output, argv.recursive
    normal_count = 0
    error_count = 0
    init(autoreset=True)
    result = os.getcwd() + '\\' + 'result'
    status_200_list = set()
    alive_403_30X_list = set()
    maybe_alive_list = set()
    other_list = set()
    dir_list = []
    urls = []
    urls2 = []
    scan_urls = []
    scan_urls2 = []
    loop = asyncio.get_event_loop()
    task3 = [asyncio.ensure_future(conn_db(loop))]
    loop.run_until_complete(asyncio.wait(task3))
    main()
    sem = asyncio.Semaphore(50)             # 最大并发量
    task = [asyncio.ensure_future(scan(url, sem)) for url in scan_urls]
    loop.run_until_complete(asyncio.wait(task))
    if len(urls2):
        task2 = [asyncio.ensure_future(scan(url, sem)) for url in scan_urls2]
        loop.run_until_complete(asyncio.wait(task2))
    cost = time.time() - start
    summ = len(scan_urls2) + len(scan_urls)
    # print(urls2)      //输出403-url
    print("共测试url:", summ)
    print("字典遍历次数：", len(urls2)+1)
    print("正常目录url数量：", len(status_200_list))
    print("403-url数量:", len(alive_403_30X_list))
    print("可能存活url数量:", len(maybe_alive_list))
    print("正常测试url:", normal_count)
    print("发生异常url:", error_count)
    print("总耗时:", cost)
