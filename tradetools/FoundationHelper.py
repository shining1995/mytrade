# !/usr/bin/python 
# -*- coding: utf-8 -*-
import time
import datetime
import glob
import urllib2
import json
import sys
import re


def get_jingzhi(strfundcode, strdate):
    try:
        url = 'http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code=' + \
              strfundcode + '&page=1&per=20&sdate=' + strdate + '&edate=' + strdate
        # print url + '\n'
        response = urllib2.urlopen(url)
    except urllib2.HTTPError, e:
        print e
        urllib_error_tag = True
    except StandardError, e:
        print e
        urllib_error_tag = True
    else:
        urllib_error_tag = False

    if urllib_error_tag == True:
        return '-1'

    json_fund_value = response.read().decode('utf-8')
    # print json_fund_value

    tr_re = re.compile(r'<tr>(.*?)</tr>')
    item_re = re.compile(
        r'''<td>(\d{4}-\d{2}-\d{2})</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?></td>''',
        re.X)

    # 获取不到 返回-1
    jingzhi = '-1'
    for line in tr_re.findall(json_fund_value):
        # print line + '\n'
        match = item_re.match(line)
        if match:
            entry = match.groups()
            print(entry)
            date = datetime.datetime.strptime(entry[0], '%Y-%m-%d')
            # jingzhi = entry[2]
            # result.append([date, float(entry[1]), entry[3]])
            jingzhi1 = entry[1]
            jingzhi2 = entry[2]
            # print jingzhi2

            if jingzhi2.strip() == '':
                # 040028
                # 净值日期	每万份收益	7日年化收益率（%）	申购状态	赎回状态	分红送配
                # 2017-01-06	1.4414												暂停申购	暂停赎回
                # 2017-01-05	1.4369												暂停申购	暂停赎回
                jingzhi = '-1'
            elif jingzhi2.find('%') > -1:
                # 040003
                # 净值日期	每万份收益	7日年化收益率（%）	申购状态	赎回状态	分红送配
                # 2017-03-27	1.1149	3.9450%	限制大额申购	开放赎回
                # 2017-03-26*	2.2240	3.8970%	限制大额申购	开放赎回
                jingzhi = '-1'
            elif float(jingzhi1) > float(jingzhi2):
                # 502015
                # 净值日期	单位净值	累计净值	日增长率	申购状态	赎回状态	分红送配
                # 2017-03-27	0.6980	0.3785	-2.24%	场内买入	场内卖出
                # 2017-03-24	0.7140	0.3945	5.15%	场内买入	场内卖出
                jingzhi = entry[1]
            else:
                #
                # 净值日期	单位净值	累计净值	日增长率	申购状态	赎回状态	分红送配
                # 2017-03-28	1.7720	1.7720	-0.23%	开放申购	开放赎回
                # 2017-03-27	1.7761	1.7761	-0.43%	开放申购	开放赎回
                jingzhi = entry[2]

    return jingzhi



if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')

    jin = get_jingzhi('000961', '2019-04-12')
    print(jin)

    # main(sys.argv)
