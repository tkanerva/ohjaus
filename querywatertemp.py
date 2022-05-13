from __future__ import print_function
from pprint import pprint
import time
from twisted.internet.task import react
import treq

APIKEY='434FE2DABC'

url='http://10.1.2.11/api/{apikey}/sensors/8'

k=1.9
b=-6
#LINEAR_EQ = k*x + b  # linear equation for value transformation. 80C at 38C. 50C at 24C.

def main(*args):
    dfr = treq.get(url.format(apikey=APIKEY), timeout=5)
    def getCurrTemp(r):
        state = r.get("state", {})
        print(state)
        t = state.get("temperature")
        x = float(t)/100.0
        temp = k*x + b
        #print(x,temp)
        from datetime import datetime
        with open("/dev/shm/temps", "a") as f:
            f.write("%s %f , %f\n" % (datetime.now().isoformat(), x, temp))
        return temp

    dfr.addCallback(treq.json_content)
    dfr.addCallback(getCurrTemp)
    return dfr

def _main(*args):
    dfr = main([])
    dfr.addCallback(print)
    def err1(f):
        return -1.0  # failure.
    dfr.addErrback(err1)
    return dfr

if __name__=="__main__":
    react(_main, [])
