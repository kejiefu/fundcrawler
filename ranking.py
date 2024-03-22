import time

import requests
import json
import pandas as pd

def greet(code):
    url = 'https://fundmobapi.eastmoney.com/FundMNewApi/FundMNNBasicInformation?deviceid=wxmp%7C49539621296d2c33e1db920d2f49fe07&version=7.5.2&product=EFund&plat=Iphone&FCODE='+code
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
                if bond_type == 1 :
                    creditDebt = item["PCTNV"]
                if bond_type == 2:
                    interestRateDebt = item["PCTNV"]
        except Exception as e:
            print(e)

        return {'编码': fcode, '类型': ftype, '名称': shortname, '信用': creditDebt, '利率': interestRateDebt}

    else:
        # 响应失败，输出错误信息
        print('Error:', response.status_code)

code_json = '015499,007333'
split_list = code_json.split(',')

data_array = []
for code in split_list:
    data = greet(code)
    time.sleep(0.2)  # 休眠200毫秒
    if data:
        data_array.append(data)
print(data_array)
# 创建 DataFrame 对象
df = pd.DataFrame(data_array)

# 将数据保存到 Excel 文件
filename = 'ranking.xlsx'
df.to_excel(filename, index=False)
print('Data saved to', filename)