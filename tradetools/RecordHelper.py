# !/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import datetime
from tradetools.FoundationHelper import get_jingzhi


class record():

    def __init__(self, id, date, base, beishu, follow, code):
        self.id = id
        self.base = float(base)
        self.beishu = float(beishu)
        self.code = code
        self.buy_date = date if date else (datetime.date.today()).strftime('%Y-%m-%d')
        self.follow = float(follow) if follow else self.base * float(beishu)
        self.jingzhi = float(get_jingzhi(code, self.buy_date))
        self.gushu = round(float(self.follow) / float(self.jingzhi) if self.jingzhi != -1 else -1, 4)


if __name__ == "__main__":
    # print(record.date)
    reload(sys)
    sys.setdefaultencoding('utf-8')
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    record = record(id=1, date=yesterday, base='100', beishu=2, follow=None, code='000961')
    print('用户id：%s 倍数：%s 日期：%s  股票代码：%s 基准金额：%s 跟投金额：%s 净值：%s 股数：%s' % (
        record.id, record.beishu, record.buy_date, record.code, record.base, record.follow,
        record.jingzhi, record.gushu))
