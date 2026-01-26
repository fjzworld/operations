# 运维平台 (Operations Platform)

现代化的企业级运维管理平台,提供资源管理、监控告警、自动化运维等核心功能。

## 技术栈

### 后端
- **FastAPI** - 高性能异步 Web 框架
- **PostgreSQL** - 关系型数据库
- **Redis** - 缓存和消息队列
- **Celery** - 分布式任务队列
- **SQLAlchemy** - ORM
- **Prometheus** - 监控指标采集

### 前端
- **Vue 3** - 渐进式 JavaScript 框架
- **TypeScript** - 类型安全
- **Element Plus** - UI 组件库
- **Vite** - 构建工具
- **ECharts** - 数据可视化
- **Pinia** - 状态管理

### 基础设施
- **Docker** - 容器化
- **Docker Compose** - 容器编排
- **Nginx** - 反向代理
- **Grafana** - 可视化监控

## 快速开始

### 前置要求
- Docker 20.10+
- Docker Compose 2.0+
- Node.js 18+ (仅用于本地开发)
- Python 3.11+ (仅用于本地开发)

### 使用 Docker Compose 启动 (推荐)

```bash
# 克隆项目
git clone <repository-url>
cd ops-platform

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

服务访问地址:
- 前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/api/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

### 本地开发

#### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动数据库 (使用 Docker)
docker-compose up -d postgres redis

# 运行开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 项目结构

```
ops-platform/
├── backend/              # 后端服务
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── core/        # 核心配置
│   │   ├── models/      # 数据模型
│   │   ├── schemas/     # Pydantic 模式
│   │   ├── services/    # 业务逻辑
│   │   └── tasks/       # Celery 任务
│   └── requirements.txt
├── frontend/            # 前端应用
│   ├── src/
│   │   ├── api/        # API 调用
│   │   ├── components/ # 组件
│   │   ├── layouts/    # 布局
│   │   ├── router/     # 路由
│   │   ├── stores/     # 状态管理
│   │   └── views/      # 页面
│   └── package.json
├── docker/             # Docker 配置
├── monitoring/         # 监控配置
└── docker-compose.yml
```

## 核心功能

### 1. 用户与权限管理
- ✅ 用户注册/登录
- ✅ JWT 认证
- ✅ 基于角色的访问控制 (RBAC)
- ✅ 操作审计日志

### 2. 资源管理 (CMDB)
- ✅ 多环境资源接入 (物理机/虚拟机/容器/云主机)
- ✅ 资源生命周期管理
- ✅ 资源标签化管理
- ✅ 资源使用率监控

### 3. 监控告警
- ✅ 多维度监控指标 (CPU/内存/磁盘)
- ✅ Prometheus 集成
- ✅ 自定义告警规则
- ✅ 多渠道告警通知
- ✅ 告警历史管理

### 4. 自动化运维
- ⏳ 脚本管理
- ⏳ 定时任务调度
- ⏳ 批量操作执行
- ⏳ CI/CD 集成

### 5. 日志与故障排查
- ⏳ 日志集中采集
- ⏳ 日志分析可视化
- ⏳ 故障定位工具

## 默认账号

首次启动后,需要创建管理员账号:

```bash
# 进入后端容器
docker-compose exec backend bash

# 创建管理员用户 (通过 API)
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "admin123",
    "role": "admin"
  }'
```

登录信息:
- 用户名: admin
- 密码: admin123

## API 文档

启动服务后访问:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## 监控

### Prometheus 指标

访问 http://localhost:8000/metrics 查看应用指标

主要指标:
- `resource_cpu_usage_percent` - 资源 CPU 使用率
- `resource_memory_usage_percent` - 资源内存使用率
- `resource_disk_usage_percent` - 资源磁盘使用率
- `total_resources` - 总资源数
- `active_resources` - 活跃资源数

### Grafana 仪表盘

访问 http://localhost:3000 (admin/admin)

## 开发指南

### 添加新的 API 端点

1. 在 `backend/app/models/` 创建数据模型
2. 在 `backend/app/schemas/` 创建 Pydantic 模式
3. 在 `backend/app/api/v1/` 创建路由
4. 在 `backend/app/main.py` 注册路由

### 添加新的前端页面

1. 在 `frontend/src/views/` 创建 Vue 组件
2. 在 `frontend/src/router/index.ts` 添加路由
3. 在 `frontend/src/api/` 添加 API 调用方法

## 常见问题

### 1. 数据库连接失败

```bash
# 检查 PostgreSQL 状态
docker-compose logs postgres

# 重启数据库
docker-compose restart postgres
```

### 2. 前端无法访问后端

检查 `frontend/vite.config.ts` 中的代理配置

### 3. Celery 任务不执行

```bash
# 检查 Celery Worker 状态
docker-compose logs celery-worker

# 重启 Worker
docker-compose restart celery-worker
```

## 贡献

欢迎提交 Issue 和 Pull Request!

## 许可证

MIT License

## 联系方式

- 项目主页: <repository-url>
- 问题反馈: <repository-url>/issues
