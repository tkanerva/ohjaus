import json
import time
from collections import defaultdict
from twisted.internet.task import react
from twisted.internet.defer import ensureDeferred
import treq
from saannot import Decision
from ohjaus_cfg import CONFIG


def dummy(*args):
    return


async def api_get(uri):
    r = await treq.get(uri)
    t = await r.text()
    return t


async def api_put(uri, payload):
    r = await treq.put(uri, json.dumps(payload).encode('ascii'))
    return r


async def get_input(item: str) -> float:
    modulename = "query{}".format(item)
    import importlib
    the_module = importlib.import_module(modulename)
    s = await the_module.main([])
    if isinstance(s, list):
        return s
    else:
        return float(s)


async def get_inputs(lst):
    d = {}
    for i in lst:
        try:
            r = await get_input(i)
        except Exception as e:
            print(e)
            r = None
        d[i] = r
    return d


async def dostuff(reactor):
    addr = CONFIG.get('DECONZ_IP')
    apikey = open(CONFIG.get('DECONZ_APIKEY')).readline().strip()

    # get inputs.
    inputs = {}
    input1 = await get_inputs(["spotprice",])
    inputs.update(input1)
    l = time.localtime()
    hour, minute, second, day = l.tm_hour, l.tm_min, l.tm_sec, l.tm_mday
    inputs.update({"hour": hour, "minute": minute, "second": second, "day": day})

    name, dev_id = "foo", CONFIG.get('RGB_LAMP_DEV_ID', 3)
    uri = CONFIG.get('DECONZ_LIGHT_URI', '').format(**locals())

    COLORS = {"green": [0.6, 0.9],
              "yellow": [0.6, 0.6],
              "orange": [0.8, 0.6],
              "red": [0.9, 0.4],
    }
    day = inputs.get('day')
    hour = inputs.get('hour')
    spotprices = inputs.get('spotprice') or []
    print("DAY, HOUR, SPOT", day, hour, spotprices)
    def process(x):
        return x.split('-')[2][0:2], x.split('-')[2].split('T')[1][0:2]
    #for ts, p in spotprices:
    #    print(ts, process(ts))
    try:
        price, *rest = [p for ts, p in spotprices if int(process(ts)[0]) == day and int(process(ts)[1]) == hour]
    except Exception as e:
        print("DEBUG: price for this hour not found!")
        price = -6.666

    payload = {"on": True} if price > -6 else {"on": False}
    print("PRICE", price)
    price_ranges = [0.0, 3.5, 8.0, 13.0]
    color_ranges = ['green', 'yellow', 'orange', 'red']
    tmp = zip(price_ranges, color_ranges)
    for threshold, c in dict(tmp).items():
        print(threshold, c)
        if price > threshold:
            color = c
        
    print("COLOR", color)
    colortuple = COLORS.get(color, [0.1, 0.1])
    payload.update({"xy": colortuple})
    print("ACCESSING: %s" % repr(uri))
    try:
        r = await api_put(uri, payload)
    except Exception:
        print("ERROR in api_put")
    print(await r.text())

    return True


def main():
    print("MAIN")
    return react(
        lambda reactor: ensureDeferred(dostuff(reactor)))


if __name__=='__main__':
    main()
