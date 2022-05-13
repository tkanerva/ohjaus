from __future__ import print_function
from pprint import pprint
from twisted.internet.task import react
from twisted.internet.threads import deferToThread
import treq


def getTeslaLevel():
    import tcharging as tc
    try:
        d = tc.main()
    except Exception as e:
        print("GOT EXCEPTION:", e)
        d = False
    if d is None:  # gave 408, meaning we need to wake it up.
        issue_wakeup()
        return None
    foo = d.get("charging_state")
    dooropen = d.get("charge_port_door_open")
    latch = d.get("charge_port_latch")
    t = [d.get("battery_level"),
         d.get("charge_limit_soc"),
         True if foo=="Charging" else False,
         dooropen,
         True if latch=="Engaged" else False,
    ]
    return t

def issue_wakeup():
    import tcommand as tcom
    try:
        tcom.main("wake")
    except Exception as e:
        print("exception while trying to wake: %s" % repr(e))


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
