import json
import time
import datetime
from collections import defaultdict
from twisted.internet.task import react
from twisted.internet.defer import ensureDeferred
import treq
from saannot import Decision
from ohjaus_cfg import CONFIG

DEFAULT_EXPIRE = 300
EXPIRES = {
    "watertemp": 60,
    "teslastate": 7200,
    "spotprice": 30,
}
CACHE = {}

def make_decision(decision_name, **inputs):
    l = time.localtime()
    hour, minute, second, day, month = l.tm_hour, l.tm_min, l.tm_sec, l.tm_mday, l.tm_mon
    inputs.update({"hour": hour, "minute": minute, "second": second, "day": day, "month": month})
    #print(inputs)
    decision_func = getattr(Decision, "decision_{}".format(decision_name))
    try:
        result, outputs = decision_func(**inputs)
    except Exception as e:
        print("EXCEPTION running decision_func.")
        print(e)
        return None, inputs
    return result, outputs


async def api_get(uri):
    r = await treq.get(uri)
    t = await r.text()
    return t


async def api_put(uri, payload):
    r = await treq.put(uri, json.dumps(payload).encode('ascii'))
    return r


class SpecialError(Exception):
    pass

async def get_input(item: str) -> float:
    # see if we should get the value from cache.
    c_item = CACHE.get(item)

    expires = CACHE.get('timestamps', {}).get(item)
    if c_item and expires and expires > time.time():
        #print("FOUND [%s] FROM CACHE: %s" % (item, c_item))
        return floatorlist(c_item)
    else:
        #print("item %s NOT FOUND in cache. OR is expired." % item)
        if expires and expires > time.time():
            print("  ...IT IS EXPIRED!")
    modulename = "query{}".format(item)
    import importlib
    the_module = importlib.import_module(modulename)
    s = await the_module.main([])
    # special value for s: None  (means an error, should retry later.)
    if s is None:
        raise SpecialError
    return floatorlist(s)

def floatorlist(s):
    if isinstance(s, list):
        return s
    else:
        return float(s)


async def get_inputs(lst):
    d = {}
    for i in lst:
        try:
            r = await get_input(i)
        except SpecialError:
            continue
        except Exception as e:
            print(e)
            r = None
        d[i] = r
        # cache the inputs. unless unchanged.
        old = CACHE.get(i)
        if r == old:
            continue
        CACHE[i] = r
        if not 'timestamps' in CACHE:
            CACHE['timestamps'] = {}
        #print("EXPIRE for %s is : %s" % (i, EXPIRES.get(i)))
        CACHE['timestamps'][i] = time.time() + EXPIRES.get(i, DEFAULT_EXPIRE)
    return d


def get_prev_state(dev_id):
    try:
        lines = open("/tmp/ohjaus.py.temp").readlines()
    except Exception:
        return None

    d = defaultdict(list)
    for line in lines:
        tmp = json.loads(line)
        history = tmp.get("history", [])
        for item in history:
            ts, item_devid, state = item
            d[item_devid].append((ts, state))
    # now we have a complete dict for every devid
    wanted = d.get(dev_id, [])
    sorted_list = list(reversed(sorted(wanted)))
    x = sorted_list[0]
    ts, state = x
    return state
    
def get_override(dev_id):
    try:
        f = open("/tmp/ohjaus.override")
    except Exception as e:
        print(e)
    else:
        try:
            d = json.load(f)
        except Exception as e:
            print(e)
            d = {}
        return d.get(str(dev_id))

async def dostuff(reactor):
    addr = CONFIG.get('DECONZ_IP')
    apikey = open(CONFIG.get('DECONZ_APIKEY')).readline().strip()

    # get inputs.
    inputs = {"current_draw": []}
    input1 = await get_inputs(["solar", "watertemp", "spotprice", "teslastate"])
    inputs.update(input1)

    reslist = []
    for name, dev_id in sorted(CONFIG.get('dev_ids').items()):
            
        res, outputs = make_decision(name, **inputs)
        reslist.append((int(time.time()), dev_id, res))
        inputs.update(outputs)  # update inputs with outputs
        
        print("%s [device id %d]: %s" % (name, dev_id, repr(res)))

        # check for overrides
        override = get_override(dev_id)
        print("OVERRIDE=%s" % override)
        if override is not None:
            payload = {"on": True if override else False}
        else:
            # read the previous state and only switch latently (do not act if we just changed state)
            prev_state = get_prev_state(dev_id)
            #print("RES, PREVSTATE = %s, %s" % (res, prev_state))
            if res != prev_state:
                print("STATE CHANGE DETECTED, going to defer action until next round.")
                continue
        if override is None:
            payload = {"on": True if res else False}

        if name == "tesla":  # special treatment. not a Zigbee device!
            import tcommand as tc
            try:
                curlevel, curlimit, already_charging, *rest = inputs.get("teslastate")
            except Exception:
                continue

            print("BATT:",curlevel, "LIMIT:", curlimit, "CHARGING:", already_charging)
            # check special condition. If limit has been set to higher than 90, disable auto control!
            if curlimit > 90:
                arg = None
            if payload.get('on') and curlimit < 80:  # NB: avoid re-setting if already set.
                arg = "SETLIMIT_" + str(90)
            elif not payload.get('on') and curlimit > 60:
                arg = "SETLIMIT_" + str(50)
            else:
                continue  # skip main() entirely
            if arg:
                tc.main(arg)
            continue

        uri = CONFIG.get('DECONZ_LIGHT_URI', '').format(**locals())
        #print("ACCESSING: %s" % repr(uri))
        r = await api_put(uri, payload)
        print(await r.text())

    # finally, store the current status in a temporary file
    data = {"history": reslist}
    with open("/tmp/ohjaus.py.temp", "a") as outf:
        json.dump(data, outf)
        outf.write('\n')
    with open("/tmp/ohjaus.cache", "wb") as outf:
        # datetime objects cannot be serialized.
        def myencode(r):
            if isinstance(r, datetime.datetime):
                return r.isoformat()
            else:
                return r
        buf = json.dumps(CACHE, default=myencode)
        outf.write(buf.encode())

    return True


def main():
    return react(
        lambda reactor: ensureDeferred(dostuff(reactor)))


if __name__=='__main__':
    try:
        f = open("/tmp/ohjaus.cache", "rb")
    except Exception:
        pass
    else:
        CACHE = json.load(f)
    main()
