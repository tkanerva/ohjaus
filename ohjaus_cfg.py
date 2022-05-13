CONFIG = {
    'DECONZ_IP': "raspbee.demotus.net",
    'DECONZ_LIGHT_URI': "http://{addr}/api/{apikey}/lights/{dev_id}/state",
    'DECONZ_APIKEY': "/home/user/raspbee.auth",

    # map: decision_name, zigbee_id
    'dev_ids': {"boileri": 2,
                "light1": 5,
                "alkutila":666,
                "tesla": 42,
    }
}
