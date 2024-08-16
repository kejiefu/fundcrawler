import json

json_data = '''[
    {"spu": "M2-DT8169"},
    {"spu": "M2-DT8179"},
    {"spu": "M2-DT8180"},
    {"spu": "M2-DT8181"},
    {"spu": "M2-TS8153"},
    {"spu": "M2-TS8136"},
    {"spu": "M2-TS8128"},
    {"spu": "M2-TS8171"},
    {"spu": "M2-TS8162"},
    {"spu": "M2-TS8172"},
    {"spu": "M2-TS8173"},
    {"spu": "M2-TS8174"},
    {"spu": "M2-TS8180"},
    {"spu": "M2-TS8177"},
    {"spu": "M2-TS8178"},
    {"spu": "M2-TS8181"},
    {"spu": "M2-TS8132"}
]'''

data = json.loads(json_data)

number_value = "10"

for item in data:
    item["number"] = number_value

json_result = json.dumps(data)
print(json_result)