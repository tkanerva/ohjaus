from __future__ import print_function
from pprint import pprint
from twisted.internet.task import react
import time
import treq
try:
    from ohjaus_cfg import CONFIG
except ImportError:
    CONFIG = {}

N_INVERTERS_EXPECTED = 14  # specify the number of inverters you have here.


def main(*args):
    url = CONFIG.get('SOLAR_URL', 'http://foo.bar/')
    dfr = treq.get(url, timeout=5)
    def getTotalPower(r):
        print('***',r)
        p = r.get('power')
        if r.get('n_inverters', N_INVERTERS_EXPECTED) < N_INVERTERS_EXPECTED-1:
            p = r.get('est_power', p)
        ts = r.get('timestamp')
        if not ts:
            return -1
        if ts < time.time()-3600:  # older than 1h?
            return -1
        return p

    def err1(f):
        print(f)
        return -1.0
  
    dfr.addCallbacks(treq.json_content, err1)
    dfr.addCallback(getTotalPower)
    return dfr

def _main(*args):
    dfr = main([])
    dfr.addCallback(print)
    dfr.addErrback(print)
    return dfr

if __name__=="__main__":
    react(_main, [])
