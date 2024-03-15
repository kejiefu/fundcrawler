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

        return {'编码': fcode, '类型': ftype, '名称': shortname}

    else:
        # 响应失败，输出错误信息
        print('Error:', response.status_code)

code_json = '015499,007333'
split_list = code_json.split(',')

data_array = []
for code in split_list:
    data = greet(code)
    if data:
        data_array.append(data)
print(data_array)
# 创建 DataFrame 对象
df = pd.DataFrame(data_array)

# 将数据保存到 Excel 文件
filename = 'ranking.xlsx'
df.to_excel(filename, index=False)
print('Data saved to', filename)