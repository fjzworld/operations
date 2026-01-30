# Release v1.1.0 - Code Quality & Security Improvements

## 版本信息
- **版本**: v1.1.0
- **发布日期**: 2026-01-30
- **主要改进**: API规范、代码质量、安全加固

---

## 改进详情

### 1. API 规范统一 (8 个端点)
- **alerts.py**: 添加 `AlertStats` 和 `MessageResponse` schema
- **resources.py**: 为所有端点添加 response_model
- **schemas/**: 新增 5 个响应模型定义

### 2. 权限检查装饰器
- **新建**: `app/core/permissions.py`
- 提供 `@require_roles()`, `@require_admin_or_operator()` 等装饰器
- 减少重复代码，提高可维护性

### 3. 类型安全
- **新建**: `frontend/src/types/user.ts`
- 定义 `User`, `UserRole`, `LoginData` 接口
- 消除前端代码中的 `any` 类型

### 4. 数据库连接池优化
- 添加 `pool_recycle=3600` - 每小时回收连接
- 添加 `pool_timeout=30` - 连接等待超时
- 添加 `echo=settings.DEBUG` - 开发环境打印 SQL

### 5. Prometheus 指标清理
- **monitoring.py**: 新增 `clear_metrics()` 和 `update_resource_status()`
- **resources.py**: 删除资源时自动清理对应指标
- 防止下线资源指标无限累积

### 6. Redis 故障日志
- **rate_limit.py**: Redis 故障时记录警告日志
- 由静默的 `pass` 改为 `logger.warning(...)`

### 7. 配置安全验证
- **config.py**: 使用 `Field()` 和 `field_validator`
- 生产环境强制要求环境变量设置 SECRET_KEY
- 检测弱密码密钥并抛出错误
- 开发环境自动生成安全密钥

### 8. 统一错误处理日志
- **monitoring.py**: `print()` → `logger.error()`
- **resources.py**: 10 处 `print()` → `logger.info/warning/error()`
- 添加 `exc_info=True` 记录完整堆栈

---

## 文件变更统计

| 类型 | 数量 | 说明 |
|------|------|------|
| 修改文件 | 11 个 | 代码改进和优化 |
| 新增文件 | 3 个 | permissions.py, user.ts |
| 新增行数 | 206 行 | 功能增强 |
| 删除行数 | 57 行 | 冗余代码清理 |

---

## 安全改进

### 配置安全
- 生产环境强制设置 SECRET_KEY
- 检测弱密码密钥
- 自动生成开发环境密钥

### 权限控制
- 统一权限检查装饰器
- 角色访问控制 (RBAC)

---

## 升级指南

### 环境变量（生产环境必需）
```bash
# 必须设置强密钥（至少32字符）
export SECRET_KEY="your-secure-random-key-min-32-chars-long"

# 可选：专用加密密钥
export ENCRYPTION_KEY="your-32-byte-base64-encoded-key"
```

### 依赖安装
```bash
cd ops-platform/backend
pip install -r requirements.txt

cd ops-platform/frontend
npm install
```

### 启动服务
```bash
# 后端
cd ops-platform/backend
python -m uvicorn app.main:app --reload

# 前端
cd ops-platform/frontend
npm run dev
```

---

## 验证清单

- [x] Python 语法验证通过
- [x] 新增模块导入测试通过
- [x] 配置文件加载测试通过
- [x] 安全警告机制生效
- [x] 代码结构验证完成

---

## 兼容性

- **后端**: Python 3.9+
- **前端**: Node.js 18+
- **数据库**: PostgreSQL 13+
- **缓存**: Redis 6+

---

## 致谢

感谢所有贡献者对本版本的改进！
