# API 接口文档

## 基础信息

- **Base URL**: `http://localhost:8000`
- **Content-Type**: `application/json`
- **认证方式**: Bearer Token (JWT)

## 认证接口

### 1. 用户登录

**POST** `/api/auth/login`

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

#### 请求示例

```json
{
  "username": "admin",
  "password": "admin123"
}
```

#### 响应示例

**成功 (200)**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**失败 (401)**

```json
{
  "detail": "Incorrect username or password"
}
```

---

### 2. 用户注册

**POST** `/api/auth/register`

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名 (3-50字符) |
| email | string | 是 | 邮箱地址 |
| full_name | string | 否 | 真实姓名 |
| password | string | 是 | 密码 |

#### 请求示例

```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "full_name": "New User",
  "password": "password123"
}
```

#### 响应示例

**成功 (201)**

```json
{
  "id": 2,
  "username": "newuser",
  "email": "newuser@example.com",
  "full_name": "New User",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-01-01T12:00:00"
}
```

**失败 (400)**

```json
{
  "detail": "Username already registered"
}
```

---

### 3. 获取当前用户信息

**GET** `/api/auth/me`

#### 请求头

```
Authorization: Bearer <token>
```

#### 响应示例

**成功 (200)**

```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "full_name": "System Administrator",
  "is_active": true,
  "is_superuser": true,
  "created_at": "2024-01-01T12:00:00"
}
```

**失败 (401)**

```json
{
  "detail": "Could not validate credentials"
}
```

---

## 用户管理接口

### 4. 获取用户列表

**GET** `/api/users/`

#### 请求参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| skip | integer | 0 | 跳过记录数 |
| limit | integer | 100 | 返回记录数 |

#### 请求头

```
Authorization: Bearer <token>
```

#### 响应示例

**成功 (200)**

```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "System Administrator",
    "is_active": true,
    "is_superuser": true,
    "created_at": "2024-01-01T12:00:00"
  },
  {
    "id": 2,
    "username": "user1",
    "email": "user1@example.com",
    "full_name": "User One",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2024-01-02T12:00:00"
  }
]
```

**失败 (403)**

```json
{
  "detail": "Not enough permissions"
}
```

---

### 5. 获取单个用户

**GET** `/api/users/{user_id}`

#### 路径参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| user_id | integer | 用户ID |

#### 请求头

```
Authorization: Bearer <token>
```

#### 响应示例

**成功 (200)**

```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "full_name": "System Administrator",
  "is_active": true,
  "is_superuser": true,
  "created_at": "2024-01-01T12:00:00"
}
```

**失败 (404)**

```json
{
  "detail": "User not found"
}
```

---

### 6. 更新用户

**PUT** `/api/users/{user_id}`

#### 路径参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| user_id | integer | 用户ID |

#### 请求头

```
Authorization: Bearer <token>
```

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| email | string | 否 | 邮箱地址 |
| full_name | string | 否 | 真实姓名 |
| password | string | 否 | 新密码 |
| is_active | boolean | 否 | 账户状态 (仅管理员) |

#### 请求示例

```json
{
  "email": "updated@example.com",
  "full_name": "Updated Name",
  "is_active": true
}
```

#### 响应示例

**成功 (200)**

```json
{
  "id": 1,
  "username": "admin",
  "email": "updated@example.com",
  "full_name": "Updated Name",
  "is_active": true,
  "is_superuser": true,
  "created_at": "2024-01-01T12:00:00"
}
```

---

### 7. 删除用户

**DELETE** `/api/users/{user_id}`

#### 路径参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| user_id | integer | 用户ID |

#### 请求头

```
Authorization: Bearer <token>
```

#### 响应

**成功 (204)**: No Content

**失败 (400)**

```json
{
  "detail": "Cannot delete yourself"
}
```

---

### 8. 获取用户统计

**GET** `/api/users/stats/count`

#### 请求头

```
Authorization: Bearer <token>
```

#### 响应示例

**成功 (200)**

```json
{
  "total_users": 10,
  "active_users": 8
}
```

---

## 仪表盘接口

### 9. 获取仪表盘统计

**GET** `/api/dashboard/stats`

#### 请求头

```
Authorization: Bearer <token>
```

#### 响应示例

**成功 (200)**

```json
{
  "total_users": 10,
  "active_users": 8,
  "admin_users": 2,
  "inactive_users": 2,
  "system_status": "operational",
  "uptime": "99.9%",
  "last_updated": "2024-01-01T12:00:00"
}
```

---

### 10. 获取最近活动

**GET** `/api/dashboard/activity`

#### 请求头

```
Authorization: Bearer <token>
```

#### 响应示例

**成功 (200)**

```json
{
  "activities": [
    {
      "type": "user_created",
      "description": "User 'newuser' was created",
      "timestamp": "2024-01-01T12:00:00",
      "user": "admin"
    }
  ]
}
```

---

## 错误代码

| HTTP 状态码 | 说明 |
|-------------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 204 | 删除成功 |
| 400 | 请求参数错误 |
| 401 | 未认证或 Token 过期 |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 使用示例

### cURL

```bash
# 登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 获取用户列表
curl -X GET http://localhost:8000/api/users/ \
  -H "Authorization: Bearer <your_token>"
```

### Python

```python
import requests

# 登录
response = requests.post(
    'http://localhost:8000/api/auth/login',
    json={'username': 'admin', 'password': 'admin123'}
)
token = response.json()['access_token']

# 获取用户列表
response = requests.get(
    'http://localhost:8000/api/users/',
    headers={'Authorization': f'Bearer {token}'}
)
users = response.json()
```

### JavaScript

```javascript
// 登录
const loginResponse = await fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: 'admin123' })
});
const { access_token } = await loginResponse.json();

// 获取用户列表
const usersResponse = await fetch('http://localhost:8000/api/users/', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const users = await usersResponse.json();
```
