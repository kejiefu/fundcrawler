import requests

url = "https://spark-api-open.xf-yun.com/v1/chat/completions"
data = {
        "model": "4.0Ultra", # 指定请求的模型
        "messages": [
            {
                "role": "user",
                "content": "你是谁"
            }
        ],
   		"stream": True
    }
header = {
    "Authorization": "Bearer xxxxxx" # 注意此处替换自己的APIPassword
}
response = requests.post(url, headers=header, json=data, stream=True)

# 流式响应解析示例
response.encoding = "utf-8"
for line in response.iter_lines(decode_unicode="utf-8"):
    print(line)