# 🤖 机器人对话系统

一个支持多机器人独立人格、群聊、文档理解、macOS 风格界面的 AI 对话系统。

## ✨ 功能特性

- **多机器人支持** - 每个机器人有独立的人格设定（系统提示词）
- **群聊模式** - 多个机器人自动互相聊天，你可以旁观或参与
- **长文档理解** - 支持上传 PDF、Word、TXT 文档，机器人可理解文档内容
- **独立对话历史** - 每个对话独立，不相互影响
- **macOS 风格界面** - 现代化深色主题设计
- **学习功能** - 机器人可在对话中学习

## 🚀 快速开始

### 前置要求

- Node.js 18+
- Python 3.9+
- OpenAI API Key（或兼容的 API）

### 1. 克隆项目

```bash
cd testforcc
```

### 2. 设置后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 复制配置文件
copy .env.example .env

# 编辑 .env 文件，填入你的 API Key
# OPENAI_API_KEY=your-api-key-here

# 启动后端服务
python -m app.main
```

后端服务将在 http://localhost:8000 运行

### 3. 设置前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将在 http://localhost:5173 运行

### 4. 使用系统

1. 打开浏览器访问 http://localhost:5173
2. 点击"新建机器人"创建你的第一个机器人
3. 为机器人设置名称和人格提示词
4. 选择预设或自定义人格
5. 开始对话！

## 📖 使用指南

### 创建机器人

1. 点击侧边栏的"+ 新建机器人"
2. 设置机器人名称
3. 选择人格预设（助手、诗人、学者、朋友、专家）或自定义
4. 设置系统提示词定义机器人行为
5. 选择使用的模型和参数
6. 保存

### 单独聊天

1. 在侧边栏选择一个机器人
2. 在对话框中发送消息
3. 机器人会基于其人格设定回复

### 群聊模式

1. 点击顶部的"群聊"标签
2. 选择 2 个或更多机器人参与群聊
3. 点击"开始群聊"
4. 机器人会自动互相聊天
5. 你可以设置自己的名字并参与对话

### 文档模式

1. 在单独聊天界面，点击"文档模式"
2. 点击文件图标上传文档（PDF、Word、TXT）
3. 上传后，机器人可以基于文档内容回答问题

## 🛠️ 技术栈

### 后端
- FastAPI - Web 框架
- LangChain - LLM 集成
- ChromaDB - 向量数据库
- SQLAlchemy - 数据库 ORM

### 前端
- React + TypeScript
- Vite - 构建工具
- Tailwind CSS - 样式
- Lucide React - 图标

## 📁 项目结构

```
testforcc/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── config.py       # 配置
│   │   ├── models.py       # 数据库模型
│   │   ├── schemas.py      # Pydantic 模型
│   │   ├── main.py         # FastAPI 应用
│   │   ├── database.py     # 数据库连接
│   │   ├── routers/         # API 路由
│   │   │   ├── bots.py      # 机器人管理
│   │   │   ├── chat.py      # 对话 API
│   │   │   ├── group_chat.py # 群聊 API
│   │   │   ├── documents.py # 文档 API
│   │   │   └── users.py    # 用户 API
│   │   └── services/       # 业务逻辑
│   │       ├── llm_service.py
│   │       ├── rag_service.py
│   │       └── group_chat_service.py
│   └── requirements.txt
│
└── frontend/               # 前端应用
    ├── src/
    │   ├── api/           # API 调用
    │   ├── components/    # React 组件
    │   ├── types/         # TypeScript 类型
    │   ├── App.tsx        # 主应用
    │   └── main.tsx       # 入口文件
    └── package.json
```

## ⚠️ 注意事项

1. **API Key** - 使用前请确保已在 `.env` 文件中配置有效的 API Key
2. **网络** - 由于使用 OpenAI API，需要稳定的网络连接
3. **费用** - 使用 API 会产生费用，请留意使用量
4. **首次运行** - 首次启动后端时会自动创建数据库

## 📄 许可证

MIT License
