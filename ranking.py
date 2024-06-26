import time

import requests
import json
import pandas as pd
import time
import random
from datetime import datetime

def greet(code):
    url = 'https://fundmobapi.eastmoney.com/FundMNewApi/FundMNNBasicInformation?deviceid=wxmp%7C49539621296d2c33e1db920d2f49fe07&version=7.5.2&product=EFund&plat=Iphone&FCODE=' + code
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36 Edg/122.0.0.0'
    }
    response = requests.get(url, headers=headers)

    # 检查响应状态码
    if response.status_code == 200:
        # 响应成功，获取响应内容
        data = response.text
        # 打印所需的参数
        print(data)

        json_data = json.loads(data)
        fcode = json_data['Datas']['FCODE']
        ftype = json_data['Datas']['FTYPE']
        fsrq = json_data['Datas']['FSRQ']
        rzdf = json_data['Datas']['RZDF']
        shortname = json_data['Datas']['SHORTNAME']

        url2 = "https://dgs.tiantianfunds.com/merge/m/api/jjxqy2"

        headers2 = {
            "Accept": "*/*",
            "validmark": "PWFszJexClxboHMMCh45qzgXFnrfdqCskGUUaGrN3L5O1fKbGaLTeAgv8Lsm1SsJbzoRFxqdk/P4qPIOge+O5A==",
            "User-Agent": "PostmanRuntime/7.26.8",
            "Host": "dgs.tiantianfunds.com",
            "Content-Length": "254"
        }

        data2 = {
            "appVersion": "6.6.12",
            "deviceid": "1E9E1896-F4C6-4653-BB42-87636FB24D12",
            "fcode": code,
            "fields": "FCODE,REPORTDATE,STYLE,WARNNUM",
            "plat": "Iphone",
            "product": "Fund",
            "serverversion": "6.6.12",
            "version": "6.6.12"
        }

        creditDebt = 0
        interestRateDebt = 0

        try:
            response2 = requests.post(url2, headers=headers2, data=data2)
            print(response2.text)
            response2Data = json.loads(response2.text)

            for item in response2Data["data"]["fundBondInvestDistri"]:
                bond_type = int(item["BONDTYPENEW"])
                if bond_type == 1:
                    creditDebt = item["PCTNV"]
                if bond_type == 2:
                    interestRateDebt = item["PCTNV"]
        except Exception as e:
            print(e)

        current_timestamp = time.time()
        milliseconds = round(current_timestamp * 1000)

        headers3 = {
            "Accept": "*/*"
        }

        url3 = (
                "https://j5.fund.eastmoney.com/sc/tfs/qt/v2.0.1/" + fcode
                + ".json?deviceid=1234567.py.service&version=6.5.5&appVersion=6.5.5&product=EFund&plat=web&curTime="
                + str(milliseconds)
        )
        response3 = requests.get(url3, headers=headers3)
        print(response3.text)
        response3Data = json.loads(response3.text)

        # 提取 title 为 Z 和 Y 的数据
        filtered_data = [item for item in response3Data["JDZF"]["Datas"] if item["title"] in ["Z", "Y"]]

        weekValue = 0
        monthValue = 0

        # 打印提取的数据
        for item in filtered_data:
            # 周收益
            if item["title"] == "Z":
                weekValue = item["syl"]
            # 月收益
            if item["title"] == "Y":
                monthValue = item["syl"]

        if ftype:
            ftype = ftype.replace("债券型-", "")

        date_str = fsrq
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%m-%d')

        return {'编码': fcode, '类型': ftype, '名称': shortname, '信用': creditDebt, '利率': interestRateDebt,
                formatted_date: rzdf,
                '周': weekValue, '月': monthValue}

    else:
        # 响应失败，输出错误信息
        print('Error:', response.status_code)


code_json = ('015499,007333,012618,012714,008974,015534,017546,003072,007195,016482,007920,004898,'
             '003177,016039,017460,010085,007677,008588,008449,010734,519720,015532,014570,004043,519783,011623')
split_list = code_json.split(',')

data_array = []
for code in split_list:
    data = greet(code)
    # 生成随机的休眠时间
    sleep_time = random.uniform(0.2, 0.3)

    # 休眠
    time.sleep(sleep_time)  # 单位为秒，根据随机生成的时间进行休眠
    if data:
        data_array.append(data)
print(data_array)

# 通过周倒序排序
sorted_data = sorted(data_array, key=lambda x: float(x['周']), reverse=True)

# 创建 DataFrame 对象
df = pd.DataFrame(sorted_data)

# 将数据保存到 Excel 文件
filename = 'ranking.xlsx'
df.to_excel(filename, index=False)
print('Data saved to', filename)
