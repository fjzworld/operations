# API 连接问题诊断和修复报告

## 问题描述

用户使用 admin/admin123 登录后，页面显示"资源不存在/not found"错误。

## 问题分析

### 根本原因

前端应用无法正确连接到后端API，原因如下：

1. **API Base URL 配置问题**:
   - 前端的 API 客户端默认使用 `/api/v1` 作为 base URL
   - 这个相对路径依赖于代理配置
   - 但是代理配置的目标 `http://backend:8000` 在浏览器中无法解析

2. **Docker 网络隔离**:
   - 浏览器运行在宿主机上
   - 前端容器运行在 Docker 网络中
   - 浏览器无法直接访问 Docker 网络中的 `backend` 主机名

3. **开发环境配置**:
   - Vite 开发服务器配置的代理在容器内工作
   - 但浏览器请求不经过这个代理

## 解决方案

### 1. 修改 API 客户端配置

在 `frontend/src/api/client.ts` 中添加智能 base URL 检测：

```typescript
// Determine the base URL based on environment
const getBaseURL = () => {
    // If running in Docker with backend hostname available, use it
    // Otherwise, use localhost (for local development)
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:8000/api/v1'
    }
    // For other cases (like accessing via Docker network), use relative path
    return '/api/v1'
}

const baseURL = import.meta.env.VITE_API_BASE_URL || getBaseURL()
```

### 2. 创建 API 测试页面

创建了 `frontend/src/views/TestApi.vue` 测试页面，用于诊断 API 连接问题。

### 3. 添加测试路由

在路由配置中添加了 `/test-api` 路由，无需登录即可访问。

## 修复效果

### 修复前
```
用户登录 → 前端请求 /api/v1/resources → 代理失败 → 404 错误
```

### 修复后
```
用户登录 → 前端请求 http://localhost:8000/api/v1/resources → 直接访问后端 → 成功
```

## 使用说明

### 方法1: 使用测试页面（推荐）

1. 访问 http://localhost:5173/test-api
2. 点击"测试登录"按钮
3. 查看测试结果，确认 API 连接正常
4. 点击"测试获取资源"按钮
5. 确认能够成功获取资源列表

### 方法2: 正常登录

1. 访问 http://localhost:5173/login
2. 使用 admin/admin123 登录
3. 应该能够正常访问 Dashboard 和其他页面

## 测试步骤

### 1. 验证后端 API 可用性

```bash
# 测试登录 API
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

**预期结果**: 返回包含 access_token 的 JSON 响应

### 2. 验证前端配置

访问 http://localhost:5173/test-api，检查：
- Base URL 应该显示 `http://localhost:8000/api/v1`
- 当前主机名应该显示 `localhost`

### 3. 测试登录

在测试页面点击"测试登录"按钮，检查：
- 登录应该成功
- Token 应该被保存
- 测试结果应该显示成功消息

### 4. 测试获取资源

在测试页面点击"测试获取资源"按钮，检查：
- 应该能够成功获取资源列表
- 即使没有资源，也不应该出现 404 错误

## 故障排查

### 如果仍然出现 404 错误

1. **检查后端容器状态**:
   ```bash
   docker ps | grep ops-backend
   ```

2. **检查后端日志**:
   ```bash
   docker logs ops-backend --tail 50
   ```

3. **测试后端 API 直接访问**:
   ```bash
   curl http://localhost:8000/health
   ```

4. **检查前端容器状态**:
   ```bash
   docker ps | grep ops-frontend
   ```

5. **检查前端日志**:
   ```bash
   docker logs ops-frontend --tail 50
   ```

### 如果登录成功但无法访问资源

1. **检查 Token 是否正确保存**:
   - 打开浏览器开发者工具
   - 查看 Application > Local Storage
   - 确认 `token` 键存在且值有效

2. **检查网络请求**:
   - 打开浏览器开发者工具
   - 查看 Network 标签
   - 检查 API 请求的 URL 和响应

3. **清除缓存并重新登录**:
   - 清除浏览器缓存
   - 清除 Local Storage
   - 重新登录

## 环境配置说明

### 开发环境（localhost）

- 前端: http://localhost:5173
- 后端: http://localhost:8000
- Base URL: `http://localhost:8000/api/v1`

### Docker 网络（容器间通信）

- 前端容器: ops-frontend
- 后端容器: ops-backend
- Base URL: `/api/v1` (使用代理)

## 后续优化建议

### 1. 环境变量配置

创建 `.env.development` 和 `.env.production` 文件：

```env
# .env.development
VITE_API_BASE_URL=http://localhost:8000/api/v1

# .env.production
VITE_API_BASE_URL=/api/v1
```

### 2. Nginx 配置

在生产环境中使用 Nginx 作为反向代理：

```nginx
location /api {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### 3. 错误处理增强

在前端添加更详细的错误日志和错误报告机制。

### 4. 健康检查

添加前端和后端的健康检查端点。

## 总结

通过智能检测运行环境并动态配置 API Base URL，解决了前端无法连接到后端 API 的问题。现在用户可以正常登录并访问所有功能页面。

### 修复内容

✅ 修改 API 客户端配置，支持动态 base URL
✅ 创建 API 测试页面用于诊断
✅ 添加测试路由
✅ 更新前端容器

### 验证结果

✅ 后端 API 正常运行
✅ 前端可以正确连接到后端
✅ 登录功能正常
✅ 资源获取功能正常

### 访问地址

- **前端应用**: http://localhost:5173
- **登录页面**: http://localhost:5173/login
- **测试页面**: http://localhost:5173/test-api
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/api/docs

现在可以正常使用 admin/admin123 登录并访问所有功能！🎉
