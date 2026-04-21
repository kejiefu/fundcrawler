# FundCrawler 代码开发规范

## 1. 项目结构规范

```
fundcrawler/
├── src/                    # 源代码目录
│   ├── __init__.py
│   ├── crawlers/           # 爬虫模块
│   │   ├── __init__.py
│   │   └── base.py         # 爬虫基类
│   ├── parsers/            # 数据解析模块
│   │   ├── __init__.py
│   │   └── base.py         # 解析器基类
│   ├── models/             # 数据模型
│   │   ├── __init__.py
│   │   └── fund.py         # 基金数据模型
│   ├── utils/              # 工具函数
│   │   ├── __init__.py
│   │   ├── logger.py       # 日志工具
│   │   └── http_client.py  # HTTP客户端封装
│   └── config/             # 配置管理
│       ├── __init__.py
│       └── settings.py     # 项目配置
├── tests/                  # 测试目录
│   ├── __init__.py
│   ├── test_crawlers/
│   └── test_parsers/
├── data/                   # 数据存储目录（运行时生成）
│   ├── raw/                # 原始数据
│   └── processed/          # 处理后数据
├── logs/                   # 日志目录（运行时生成）
├── scripts/                # 脚本目录
├── requirements.txt        # 依赖清单
├── setup.py                # 安装配置
├── pyproject.toml          # 现代Python项目配置
├── .gitignore
└── README.md
```

## 2. 命名规范

### 2.1 模块和包命名
- **模块名**：使用小写字母和下划线，如 `http_client`、`fund_parser`
- **包名**：使用小写字母，尽量简短，如 `crawlers`、`parsers`
- **避免**：单字符模块名（除非是临时脚本）

### 2.2 类命名
- **类名**：采用 PascalCase 风格，如 `FundSpider`、`DataParser`
- **基类**：以 `Base` 结尾或开头，如 `BaseSpider`、`BaseParser`
- **异常类**：以 `Error` 结尾，如 `CrawlError`、`ParseError`

### 2.3 函数命名
- **函数名**：使用小写字母和下划线，如 `fetch_page`、`parse_fund_data`
- **私有函数**：以下划线开头，如 `_validate_response`
- **异步函数**：以 `async_` 前缀，如 `async_fetch_data`

### 2.4 变量命名
- **普通变量**：小写字母和下划线，如 `fund_code`、`page_content`
- **类属性**：小写字母和下划线
- **私有属性**：以下划线开头
- **常量**：全大写，如 `MAX_RETRY_COUNT`、`DEFAULT_TIMEOUT`

### 2.5 常量与配置
```python
# 合理的常量命名
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30
REQUEST_DELAY = 1.0

# 不推荐的命名
MAX = 3
TIMEOUT = 30
```

## 3. 代码格式规范

### 3.1 缩进与空格
- 使用 **4 个空格** 进行缩进
- 二元运算符两侧加空格：`a + b`
- 逗号、冒号后面加空格：`func(a, b)`
- 关键字参数：`func(key=value)`
- 不在括号内侧加空格：`func(a)` 而非 `func( a )`

### 3.2 行长度
- 单行不超过 **120 个字符**
- 长表达式可换行，保持缩进一致

### 3.3 导入顺序
```python
# 1. 标准库
import os
import sys
import json
from datetime import datetime

# 2. 第三方库
import requests
from bs4 import BeautifulSoup
import pandas as pd

# 3. 本地模块（相对导入）
from .utils import logger
from ..config import settings
```

### 3.4 空行使用
- 模块顶级定义之间：两个空行
- 类方法之间：一个空行
- 函数内逻辑段落之间：一个空行

## 4. 函数设计规范

### 4.1 函数长度
- 单个函数不超过 **50 行**
- 如果函数过长，考虑拆分为多个子函数

### 4.2 参数设计
```python
# 推荐：明确的参数名
def fetch_fund_data(fund_code: str, date: str) -> dict:
    pass

# 推荐：使用 *args 和 **kwargs 时确保有默认值
def batch_process(items: list, *args, **kwargs):
    pass
```

### 4.3 返回值
- 函数应保持单一的返回点（尽量）
- 明确返回类型注解
```python
def parse_fund_price(price_str: str) -> Optional[float]:
    pass
```

## 5. 类设计规范

### 5.1 类的结构顺序
```python
class FundSpider:
    # 1. 类变量/类常量
    DEFAULT_HEADERS = {...}

    # 2. __init__ 方法
    def __init__(self, config: dict):
        self.config = config
        self._setup()

    # 3. 公共方法
    def crawl(self, fund_code: str) -> dict:
        pass

    # 4. 私有方法
    def _setup(self):
        pass

    # 5. 特殊方法（__str__, __repr__等）
    def __repr__(self):
        return f"FundSpider({self.config})"
```

### 5.2 继承与接口
- 优先使用组合而非继承
- 明确标注 override 的方法
- 基类定义清晰的接口文档

## 6. 异常处理规范

### 6.1 自定义异常
```python
class FundCrawlerError(Exception):
    """基础异常类"""
    pass

class NetworkError(FundCrawlerError):
    """网络相关异常"""
    pass

class ParseError(FundCrawlerError):
    """解析数据异常"""
    pass
```

### 6.2 异常捕获
```python
# 推荐：具体异常捕获
try:
    response = requests.get(url, timeout=10)
except requests.Timeout:
    logger.error(f"请求超时: {url}")
    raise NetworkError(f"请求超时: {url}")
except requests.RequestException as e:
    logger.error(f"请求失败: {e}")
    raise NetworkError(f"请求失败: {e}")

# 不推荐：捕获所有异常
try:
    response = requests.get(url)
except:
    pass
```

### 6.3 异常传播
- 允许异常向上传播，不要过度捕获
- 在捕获处记录完整日志
- 保留原始异常信息

## 7. 日志规范

### 7.1 日志级别使用
```python
logger.debug("调试信息：详细执行流程")
logger.info("普通信息：正常业务流程")
logger.warning("警告信息：潜在问题但不影响运行")
logger.error("错误信息：操作失败")
logger.critical("严重错误：系统级问题")
```

### 7.2 日志格式
```python
import logging

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 8. 注释规范

### 8.1 文档字符串 (Docstring)
```python
class FundSpider:
    """基金爬虫类，负责从指定来源获取基金数据。

    该类提供标准的爬取接口，支持重试机制和错误处理。

    Attributes:
        config: 爬虫配置字典
        retry_count: 最大重试次数
    """

    def crawl(self, fund_code: str) -> dict:
        """爬取指定基金的数据。

        Args:
            fund_code: 基金代码，如 '000001'

        Returns:
            包含基金数据的字典对象

        Raises:
            NetworkError: 网络请求失败
            ParseError: 数据解析失败
        """
        pass
```

### 8.2 行内注释
- 避免明显的注释：`x = x + 1  # x 加 1`
- 保留有价值的注释：解释 **为什么** 而非 **是什么**

## 9. 类型注解规范

### 9.1 函数类型注解
```python
from typing import Optional, List, Dict, Union

def process_funds(
    fund_codes: List[str],
    start_date: str,
    end_date: Optional[str] = None
) -> Dict[str, dict]:
    """处理基金数据"""
    pass
```

### 9.2 常用类型
```python
Optional[X]        # 等价于 X | None
List[X]            # 列表类型
Dict[K, V]         # 字典类型
Union[A, B]        # 联合类型
Callable[[A, B], C]  # 可调用对象类型
```

## 10. 配置管理规范

### 10.1 配置文件结构
```python
# config/settings.py
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 爬虫配置
CRAWLER_CONFIG = {
    "timeout": 30,
    "max_retry": 3,
    "delay": 1.0,
}

# 数据库配置（如有）
DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
}
```

### 10.2 敏感信息处理
- 敏感配置使用环境变量
- 不在代码中硬编码密码、密钥
- 提供 `config.example.py` 作为模板

## 11. 依赖管理规范

### 11.1 requirements.txt 示例
```
requests>=2.28.0
beautifulsoup4>=4.11.0
pandas>=1.5.0
lxml>=4.9.0
```

### 11.2 依赖安装
```bash
pip install -r requirements.txt
```

## 12. Git 提交规范

### 12.1 Commit 消息格式
```
<type>: <subject>

<body>
```

示例：
```
feat: 添加基金数据爬取功能

- 实现 FundSpider 类
- 添加数据解析器
- 集成日志模块

Closes #123
```

### 12.2 Type 类型
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

## 13. 测试规范

### 13.1 测试文件命名
```
tests/
├── test_crawlers/
│   ├── __init__.py
│   └── test_fund_spider.py
├── test_parsers/
│   └── test_fund_parser.py
└── conftest.py
```

### 13.2 测试用例规范
```python
import pytest

class TestFundSpider:
    """基金爬虫测试类"""

    def test_fetch_fund_success(self, mock_response):
        """测试成功获取基金数据"""
        spider = FundSpider()
        result = spider.crawl("000001")
        assert result["code"] == "000001"
        assert "price" in result

    def test_fetch_fund_not_found(self):
        """测试基金代码不存在的情况"""
        spider = FundSpider()
        with pytest.raises(FundNotFoundError):
            spider.crawl("INVALID")
```

## 14. 代码审查要点

### 14.1 自查清单
- [ ] 代码是否符合命名规范
- [ ] 函数是否过于复杂（超过50行）
- [ ] 是否有完整的类型注解
- [ ] 异常处理是否得当
- [ ] 日志记录是否充分
- [ ] 是否有硬编码的值需要提取为常量
- [ ] 是否有不必要的注释
- [ ] 测试是否覆盖关键逻辑

### 14.2 Review 关注点
- 代码可读性和可维护性
- 边界条件和异常情况处理
- 性能考虑（大量数据处理场景）
- 安全问题（注入、XSS等）

---

## 附录：A. 不推荐的做法

```python
# ❌ 不推荐的写法
def process(d, k, v):  # 缺乏类型注解和语义命名
    if k in d.keys():  # 冗余的 .keys()
        d[k] = v
    return d

# ✅ 推荐写法
def update_dict(data: dict, key: str, value: Any) -> dict:
    """更新字典中的值"""
    data[key] = value
    return data
```

---

**版本**：1.0.0
**最后更新**：2026-04-21
**维护人**：fundcrawler team
