from __future__ import print_function
from pprint import pprint
from twisted.internet.task import react
from twisted.internet.threads import deferToThread
import treq


def getTeslaLevel():
    import tcharging as tc
    d = tc.main()
    return d.get("battery_level")
  
def main(*args):
    #dfr = treq.get(url)
    dfr = deferToThread(getTeslaLevel)
    return dfr

def _main(*args):
    dfr = main([])
    dfr.addCallback(print)
    dfr.addErrback(print)
    return dfr

if __name__=="__main__":
    react(_main, [])
