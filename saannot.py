class Decision:

    @staticmethod
    def decision_alkutila(**i):
        takes = 2600
        hour = i.get('hour')
        day = i.get('day')
        spotprices = i.get('spotprice') or []
        def _ts_day(x):
            y, m, d = x[0:10].split('-')
            return int(d)
        def _ts_hr(x):
            H, M, S = x[11:].split(':')
            return int(H)
        try:
            price, *rest = [p for ts, p in spotprices if _ts_day(ts) == day and _ts_hr(ts) == hour]
        except Exception:
            print("DEBUG: hourly price not found for this moment!")
            price = 6.666
        new = i.copy()
        new.update({"current_draw": [takes]})
        print("PRICE ============= %s"%price)
        if price > 8:  # do we get more money selling the electricity than storing it?
            print("ELECTRICITY EXPENSIVE, selling some kwh", price)
            return True, new
        return False, i


    @staticmethod
    def decision_tesla(**i):
        takes = 1300
        day = i.get('day')
        hour = i.get('hour')
        teslastate = i.get('teslastate') or [False]*5
        solar = i.get('solar') or -1
        spotprices = i.get('spotprice') or []
        consumption = i.get('current_draw', [])
        import datetime
        month = datetime.datetime.now().month
        remaining_solar = solar - sum(consumption)  # it is a list of items
        print("REMAINING_SOLAR : %s" % remaining_solar)
        new = i.copy()
        new.update({"current_draw": consumption + [takes]})
        
        battlevel, chargelimit, charging, dooropen, latch, *rest = teslastate
        print("TESLASTATE: door_open: %s , latch: %s" % (dooropen, latch))
        # check if we can charge the car (is it connected to charger?)
        #if not dooropen or not latch:
        #    return False, i  # cannot charge.

        # if spot price is very low, take advantage
        try:
            print("TS=", spotprices[0].split('-'))
        except Exception:
            pass
        try:
            #price, *rest = [p for ts, p in spotprices if ts.split('-')[2] == day and ts.hour == hour]
            price, *rest = [p for ts, p in spotprices if ts.split('-')[2][0:2] == str(day) and ts.split('-')[2].split('T')[1][0:2] == str(hour)]
        except Exception:
            print("DEBUG: price for this hour not found!")
            price = 6.666

        if remaining_solar > 1100 and 0 <= hour < 4:  # WINTER: nighttime.
            return True, new  # we get half the power from solar

        if price < 3.5 and battlevel < 75:  # very cheap!
            return True, new
        if price < 0.5 and battlevel < 85:  # very cheap!
            return True, new

        # if it is night and current charge level is below 60, use night tariff
        if 2 <= hour < 7:
            return True, new
        if battlevel < 65 and (0 <= hour < 2):
            return True, new

        return False, i


    @staticmethod
    def decision_boileri(**i):
        
        # avg maximums of each month
        import datetime
        n=datetime.datetime.now()

        month_max = [10, 10, 500, 1000, 2500, 2500, 2500, 2000, 1200, 500, 100, 10]
        takes = 2500  # in watts
        watermax = 80.0
        waterlowlimit = 42.0
        day = i.get('day')
        hour = i.get('hour')
        solar = i.get('solar') or -1
        water = i.get('watertemp') or 9999
        spotprices = i.get('spotprice') or []
        consumption = i.get('current_draw', [])
        month = i.get('month', 1)
        month = n.month
        max_solar = month_max[month-1]
        remaining_solar = solar - sum(consumption)  # it is a list of items
        new = i.copy()
        new.update({"current_draw": consumption + [takes]})
        # if spot price is very low, take advantage
        try:
            spot_sorted = sorted(spotprices, key=lambda x: x[0])
        except Exception:
            print("EXCEPTION 1")
            spot_sorted = []
        #print("SORTED:", spot_sorted)
        this_hour = datetime.datetime.now().replace(minute=0)
        try:
            next_day = datetime.datetime.now().replace(day=this_hour.day+1, hour=0, minute=0)
        except Exception:
            next_day = datetime.datetime.now().replace(day=1, hour=0, minute=0, month=this_hour.month+1)
        tmp = [p for ts, p in spot_sorted if ts >= this_hour.isoformat() and ts < next_day.isoformat()]
        tmp2 = [p for ts, p in spotprices if ts >= this_hour.isoformat() and ts < next_day.isoformat()]

        if tmp and spot_sorted:
            cheapest, *rest = [ts for ts, p in spot_sorted if p == min(tmp)]
        elif spot_sorted:
            cheapest = spotprices[0][0]
        else:
            cheapest = (this_hour.replace(hour=0)).isoformat()

        print("CHEAPEST is " , cheapest)
        try:
            price, price_next, *rest = tmp2
        except Exception:
            print("DEBUG: price for this hour not found!")
            price, price_next = 6.666, 6.6

        #print([ts.split('-')[2].split('T')[1][3:5] for ts, p in spotprices])
        try:
            price, *rest = [p for ts, p in spotprices if ts.split('-')[2][0:2] == str(day) and ts.split('-')[2].split('T')[1][0:2] == str(hour)]
        except Exception as e:
            price = 6.66

        print("PRICE, PRICE_NEXT: %s , %s" % (price,price_next))

        # warm an extra hour, just in case.
        if hour == 23 or hour == 0 or hour == 1:  # 10 = 13EEST  01=04 EEST
            return True, new

        if hour == 12 and price < 5:  # we get solar?
            return True, new

        if 13 <= hour < 17:
            return False, i  # this goes to tesla. TODO: check whether tesla is charging.

        if price < 0.90: # and water < watermax-10:  # very cheap!
            return True, new

        # if the next hour is going to be very expensive, pre-heat!
        if price_next > 12.00 and price < 6.50:
            return True, new
        
        # if water is too cold, do something to avoid wrath of the family
        if water < waterlowlimit:
            return True, new

        if 10 <= hour < 12 and water < watermax-10:  # 00-02 eet SUMMER: 14-15 UTC+3
            return True, new

        print("hour:",hour,datetime.datetime.fromisoformat(cheapest))
        if hour == datetime.datetime.fromisoformat(cheapest).hour:  # warm 1 extra hour. choose the cheapest hour.
            return True, new

        if water < 48 and remaining_solar > 1000:
            return True, new  # if temp is rather low, and we get decent solar, warm it up

        if remaining_solar > 2000 and water < watermax:
            return True, new

        # if its winter and there is too little sun, fall early.
        if max_solar < 500 and price > 3.0:
            return False, i

        if max_solar < 500 and price <= 3.0 or (max_solar < 500) and hour == 1:  # at night, 3am
            return True, new
            
        if max_solar > takes*0.5 and remaining_solar > max_solar*0.8 and 9 <= hour <= 11 and (water < 45 or water == 9999):  # 11-14 EEST
            return True, new

        return False, i


    @staticmethod
    def decision_light1(**i):
        takes = 5
        hour = i.get('hour') or 0
        solar = i.get('solar') or -1
        consumption = i.get('current_draw', [])
        remaining_solar = solar - sum(consumption)  # it is a list of items
        if 12 <= hour <= 20:
            return True, i
        else:
            return False, i


    @staticmethod
    def decision_zzz(**i):
        # this is the last in chain. Will decide where to put excess energy.
        takes = 5000
        hour = i.get('hour') or 0
        solar = i.get('solar') or -1
        consumption = i.get('current_draw', [])
        remaining_solar = solar - sum(consumption)  # it is a list of items
        if remaining_solar > 2000:
            return True, i
        else:
            return False, i
