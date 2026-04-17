# Intelligent-News-Assistant (智能新闻助手)

基于大语言模型（LLM）和检索增强生成（RAG）技术的智能新闻推荐与问答系统。

## 项目特点

- **新闻爬取与处理**: 抓取新闻RSS（澎湃、新浪等），自动提取正文内容，并使用大语言模型（LLM）对内容进行智能审核、摘要提取及标签分类，有效拦截垃圾内容。
- **智能推荐系统**: 基于用户行为（阅读、点赞）和用户画像，提供个性化的新闻推荐。
- **智能问答 (RAG)**: 结合新闻知识库（ChromaDB）和LLM，提供基于新闻内容的智能问答。
- **前后端分离架构**: 后端使用FastAPI，前端使用Vue 3。

## 核心技术栈

### 后端 (Backend)
- **框架**: FastAPI
- **数据库**: SQLite (关系型数据) + ChromaDB (向量数据库)
- **数据抓取**: BeautifulSoup4, feedparser
- **AI / RAG**: 文本向量化 (Embedding)，大模型接口集成
- **核心模块**:
  - `routers/`: 包含用户、新闻、推荐、聊天、互动和爬虫等 API 路由。
  - `services/`: 包含 RAG 会话服务、推荐算法、向量存储、LLM 调用等核心业务逻辑。
  - `scraper/`: 新闻抓取与清洗管道，包含基于 LLM 的内容质量审核机制。
  - `models/`: 数据库 ORM 模型。

### 前端 (Frontend)
- **框架**: Vue 3
- **构建工具**: Vite
- **路由**: Vue Router
- **页面视图**:
  - `NewsList.vue`: 新闻列表页
  - `NewsDetail.vue`: 新闻详情页
  - `Recommend.vue`: 个性化推荐页
  - `Chat.vue`: 智能问答对话页
  - `Login.vue`: 用户登录注册页

## 快速开始

### 后端配置与启动

1. 进入 `backend` 目录
2. 复制环境变量文件并配置所需的 API Key：
   ```bash
   cp .env.example .env
   ```
3. 安装 Python 依赖：
   ```bash
   pip install -r requirements.txt
   ```
4. 启动 FastAPI 服务：
   ```bash
   python main.py
   ```
   *服务默认运行在 http://localhost:8000*

### 前端配置与启动

1. 进入 `frontend` 目录
2. 安装 Node 依赖：
   ```bash
   npm install
   ```
3. 启动开发服务器：
   ```bash
   npm run dev
   ```

## API 文档

后端服务启动后，可以访问以下地址查看完整的 API 接口文档（Swagger UI）：
- `http://localhost:8000/docs`
