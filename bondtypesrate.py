import requests

url = "https://dgs.tiantianfunds.com/merge/m/api/jjxqy2"

headers = {
    "Accept": "*/*",
    "validmark": "PWFszJexClxboHMMCh45qzgXFnrfdqCskGUUaGrN3L5O1fKbGaLTeAgv8Lsm1SsJbzoRFxqdk/P4qPIOge+O5A==",
    "User-Agent": "PostmanRuntime/7.26.8",
    "Host": "dgs.tiantianfunds.com",
    "Content-Length": "254"
}

data = {
    "appVersion": "6.6.12",
    "deviceid": "1E9E1896-F4C6-4653-BB42-87636FB24D12",
    "fcode": "015499",
    "fields": "FCODE,REPORTDATE,STYLE,WARNNUM",
    "plat": "Iphone",
    "product": "Fund",
    "serverversion": "6.6.12",
    "version": "6.6.12"
}

try:
    response = requests.post(url, headers=headers, data=data)
    print(response.ok)
    print(response.text)
except Exception as e:
    print(e)
