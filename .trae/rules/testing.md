## 测试代码组织规范

### 1. 测试目录结构

项目中的所有测试代码应统一存放在根目录下的 `tests/` 文件夹中：

```
tests/
├── backend/           # 后端测试代码
│   ├── test_*.py      # 单元测试文件
│   └── fixtures/      # 测试数据和配置
└── frontend/          # 前端测试代码
    ├── test_*.js      # JavaScript 测试文件
    └── __tests__/     # Vue 组件测试
```

### 2. 文件命名规范

| 文件类型 | 命名模式 | 示例 |
|---------|---------|------|
| 后端单元测试 | `test_*.py` | `test_kline_sync.py` |
| 前端单元测试 | `test_*.js` | `test_api.js` |
| Vue 组件测试 | `*.spec.js` | `StockDetail.spec.js` |
| 测试工具/辅助函数 | `*_helper.py` 或 `conftest.py` | `test_helper.py` |

### 3. 测试代码分类

#### 3.1 后端测试 (`tests/backend/`)
- 数据库操作测试
- API 接口测试
- 业务逻辑测试
- 定时任务测试

#### 3.2 前端测试 (`tests/frontend/`)
- 组件功能测试
- API 调用测试
- 页面路由测试
- UI 交互测试

### 4. 测试代码规范

#### 4.1 代码风格
- 遵循项目主代码的编码规范
- 使用清晰的测试用例命名
- 每个测试函数应独立、可重复执行

#### 4.2 测试数据
- 测试数据应放在 `fixtures/` 目录下
- 避免在测试代码中硬编码大量测试数据
- 使用 mock 对象替代外部依赖

### 5. 测试运行

```bash
# 运行所有后端测试
cd tests/backend
python -m pytest

# 运行特定测试文件
python -m pytest test_kline_sync.py

# 运行前端测试
cd tests/frontend
npm test
```

### 6. 注意事项

- 测试代码不应提交生产环境
- 测试文件不应包含敏感信息（如数据库密码）
- 保持测试代码与生产代码同步更新
- 每个新功能应配套相应的测试用例