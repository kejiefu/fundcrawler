data = {
    "JDZF": {
        "Datas": [
            {"title": "Z", "syl": "0.04", "avg": "0.05", "hs300": "-0.95", "rank": "549", "sc": "828", "diff": "143"},
            {"title": "Y", "syl": "0.21", "avg": "0.22", "hs300": "2.62", "rank": "254", "sc": "827", "diff": "51"},
            {"title": "3Y", "syl": "1.06", "avg": "1.12", "hs300": "6.59", "rank": "343", "sc": "820", "diff": "21"},
            {"title": "6Y", "syl": "1.99", "avg": "1.84", "hs300": "-4.04", "rank": "163", "sc": "787", "diff": "0"},
            {"title": "1N", "syl": "3.79", "avg": "3.52", "hs300": "-12.00", "rank": "180", "sc": "734", "diff": "-2"},
            {"title": "2N", "syl": "", "avg": "6.41", "hs300": "-15.11", "rank": "", "sc": "524", "diff": ""},
            {"title": "3N", "syl": "", "avg": "10.12", "hs300": "-29.66", "rank": "", "sc": "336", "diff": ""},
            {"title": "5N", "syl": "", "avg": "16.95", "hs300": "-4.23", "rank": "", "sc": "145", "diff": ""},
            {"title": "JN", "syl": "0.89", "avg": "0.94", "hs300": "3.28", "rank": "325", "sc": "820", "diff": "8"},
            {"title": "LN", "syl": "7.21", "avg": "", "hs300": "", "rank": "", "sc": "", "diff": ""}
        ],
        "ErrCode": 0,
        "Success": True,
        "ErrMsg": None,
        "Message": None,
        "ErrorCode": "0",
        "ErrorMessage": None,
        "ErrorMsgLst": None,
        "TotalCount": 10,
        "Expansion": {
            "ESTABDATE": "2022-04-11",
            "TIME": "2024-03-25",
            "ISUPDATING": False
        }
    }
}

# 提取 title 为 Z 和 Y 的数据
filtered_data = [item for item in data["JDZF"]["Datas"] if item["title"] in ["Z", "Y"]]
print(filtered_data)

# 打印提取的数据
for item in filtered_data:
    if item["title"] == "Z":
        print(item["syl"])
    if item["title"] == "Y":
        print(item["syl"])

