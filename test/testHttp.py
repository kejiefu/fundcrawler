import json
import time

import requests

current_timestamp = time.time()
milliseconds = round(current_timestamp * 1000)

headers2 = {
    "Accept": "*/*"
}

url3 = "https://j5.fund.eastmoney.com/sc/tfs/qt/v2.0.1/" + "015499" + ".json?deviceid=1234567.py.service&version=6.5.5&appVersion=6.5.5&product=EFund&plat=web&curTime=" + str(
    milliseconds)
response3 = requests.get(url3, headers=headers2)
print(response3.text)
response3Data = json.loads(response3.text)
