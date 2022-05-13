#!/usr/bin/python3
#import treq
from __future__ import print_function
import requests
import json
from functools import partial
from datetime import datetime, date
from twisted.internet.task import react
import treq


URL="http://sahko.tk"
ENCODING="ISO-8859-1"

def get_stuff():
    r = requests.get(URL)
    return r.text


def main(*args):
    dfr = treq.get(URL, timeout=5)
    def getPriceLine(r):
        for line in r.splitlines():
            if ";var data1=" in line:
                idx1 = line.index(";var data1=")
                tmp1 = line[idx1:]
                foobar, _, rawdata_ = tmp1.partition('=')
                idx2 = rawdata_.index(";")
                rawdata = rawdata_[:idx2]
                break
        else:
            rawdata = ""
        # chop off data2
        S1 = ",data2"
        idx3 = rawdata.index(S1)
        rawdata = rawdata[:idx3]
        return rawdata.replace(';','')

    def processPrices(r):
        # eats a json string
        data = json.loads(r)
        l = []
        for timestamp, price in data:
            # timestamps are unix epoch in milliseconds, shifted to UTC+3
            tmp = timestamp/1000 - (3*3600)  # HARDCODED. fixme.
            # drop prices that are older than today
            dt = datetime.fromtimestamp(tmp)
            today = date.today()
            if dt.date() >= today:
                l.append((datetime.fromtimestamp(tmp).isoformat(), price))
        return l

    cb = partial(treq.text_content, encoding=ENCODING)
    dfr.addCallback(cb)
    #dfr.addCallback(treq.text)
    dfr.addCallback(getPriceLine)
    dfr.addCallback(processPrices)
    return dfr

def _main(*args):
    dfr = main([])
    dfr.addCallback(print)
    return dfr

if __name__=='__main__':
    react(_main, [])
