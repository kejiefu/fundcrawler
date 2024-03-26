import pandas as pd
import matplotlib.pyplot as plt

data = [{'编码': '015499', '类型': '债券型-中短债', '名称': '东海祥苏短债E'}, {'编码': '007333', '类型': '债券型-长债', '名称': '嘉合磐昇纯债C'}]

# 将数组转换为Pandas DataFrame
df = pd.DataFrame(data)

# 使用matplotlib将DataFrame绘制为表格并保存为图片
fig, ax = plt.subplots()
ax.axis('off')
table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc='center', loc='center')

# 设置全局字体属性
plt.rcParams['font.sans-serif'] = ['SimHei']  # 替换成你系统中支持中文的字体，如黑体或宋体

table.auto_set_font_size(False)
table.set_fontsize(14)
table.scale(1, 1.5)

plt.savefig('table_image.png', bbox_inches='tight', dpi=300)
plt.show()