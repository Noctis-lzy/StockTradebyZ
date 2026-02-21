# 股票交易系统 Web 版

## 项目结构

```
StockTradebyZ/
├── backend/          # FastAPI 后端
├── frontend/         # React 前端
└── data/            # 股票数据
```

## 快速开始

### 后端启动

1. 进入后端目录：
```bash
cd backend
```

2. 创建虚拟环境（推荐）：
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 启动后端服务：
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端 API 文档：http://localhost:8000/docs

### 前端启动

1. 进入前端目录：
```bash
cd frontend
```

2. 如果遇到 npm 缓存权限问题，先修复：
```bash
sudo chown -R $(whoami) ~/.npm
npm cache clean --force
```

3. 安装依赖：
```bash
npm install --legacy-peer-deps
```

4. 启动前端服务：
```bash
npm run dev
```

前端访问地址：http://localhost:3000

## 默认账号

- 用户名：admin
- 密码：admin123

## 功能模块

### 2.1 登录认证
- 用户登录功能
- 路由守卫（未登录时跳转登录页）

### 2.2 个人工具箱
- 工具箱首页
- 基础页面框架

### 2.3 选股工具模块（规划中）
- 股票筛选功能
- 股票分析功能

### 2.4 批量回测工具模块（规划中）
- 策略配置功能
- 回测执行功能

### 2.5 个股回测工具模块（规划中）
- 个股选择功能
- 策略配置功能
- 回测执行功能
- 买卖点分析功能

## 技术栈

### 后端
- FastAPI
- Python 3.x
- JWT 认证

### 前端
- React 18
- Ant Design
- React Router
- Axios
- Recharts（图表库）
