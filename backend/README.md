# 🧠 智能新闻助手 - 后端开发指南

欢迎加入智能新闻助手项目！作为后端架构师，我已经完成了项目的基础框架搭建。请按照以下步骤配置本地开发环境，确保所有成员使用一致的 Python 版本和依赖。

---

## 一、项目结构

```
intelligent-news-assistant/
├── backend/                # 后端代码
│   ├── main.py            # FastAPI 应用入口
│   ├── database.py        # 数据库连接配置
│   ├── models/            # 数据库模型（User, Article, Interaction）
│   ├── routers/           # API 路由（待开发）
│   ├── services/          # 业务逻辑（待开发）
│   ├── scraper/           # 新闻采集模块（成员C）
│   ├── .env.example       # 环境变量模板
│   ├── requirements.txt   # Python 依赖列表
│   └── venv/              # 虚拟环境（本地生成，不提交）
└── frontend/              # 前端代码（成员D）
```

---

## 二、环境要求

- **Python 3.10.11**（必须，版本不一致可能导致依赖安装失败或运行异常）
- **Git**（用于克隆仓库）
- 可选：PostgreSQL 客户端（如果计划测试远程数据库）

---

## 三、克隆仓库

```bash
git clone <仓库地址>
cd intelligent-news-assistant/backend
```

---

## 四、配置后端环境

### 1. 创建并激活虚拟环境

- **Windows**（PowerShell）：
  ```bash
  py -3.10 -m venv venv
  .\venv\Scripts\activate
  ```
- **macOS / Linux**：
  ```bash
  python3.10 -m venv venv
  source venv/bin/activate
  ```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env`，并填入自己的值：

```bash
cp .env.example .env
```

编辑 `.env`，至少需要配置：

- `ZHIPU_API_KEY`：智谱 AI 的 API Key（注册获取：https://bigmodel.cn/）
- `DATABASE_URL`：本地默认使用 `sqlite:///./news.db`，无需修改
- `CORS_ORIGINS`：本地开发使用 `http://localhost:5173`（前端默认端口）

### 4. 初始化数据库

运行后端时会自动创建 SQLite 数据库文件 `news.db`，无需手动操作。

---

## 五、启动后端服务

```bash
uvicorn main:app --reload

或指定端口
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

服务启动后，访问：

- API 文档：http://localhost:8000/docs
- 根路径：http://localhost:8000（返回 `{"message":"Hello World"}`）

---

## 六、其他成员任务对接

### 成员C（数据工程师）

- 导入 `models.article.Article` 和 `database.get_db` 进行数据入库。
- 编写采集接口 `POST /api/crawl/start`，存放在 `routers/crawl.py`。

### 成员B（AI工程师）

- 在 `services/` 下实现 `llm_service.py`、`embedding_service.py`、`rag_service.py`、`vector_store.py`。
- 提供 `POST /api/chat` 接口（`routers/chat.py`）。
- 提供推荐服务函数 `get_recommendations(user_id, limit)` 供成员A调用。

### 成员E（后端业务工程师）

- 在 `models/user.py` 基础上实现用户认证（JWT）。
- 实现 `POST /api/user/register`、`POST /api/user/login`。
- 实现点赞接口 `POST /api/like` 和用户画像相关逻辑。

### 成员D（前端工程师）

- 前端开发时，确保 API 请求地址为 `http://localhost:8000`。
- 跨域问题已在后端配置 CORS，允许 `http://localhost:5173` 访问。

---

## 七、常见问题

### 1. Python 版本不是 3.10.11

- 请安装 Python 3.10.11（[官网下载](https://www.python.org/downloads/release/python-31011/)），并使用 `py -3.10` 或 `python3.10` 命令创建虚拟环境。

### 2. 运行 `pip install -r requirements.txt` 报错

- 确保虚拟环境已激活。
- 尝试升级 pip：`python -m pip install --upgrade pip`

### 3. 数据库表未自动创建

- 检查 `main.py` 中是否包含 `Base.metadata.create_all(bind=engine)`（已包含，无需修改）。
- 确保 `models/` 下的模型已正确导入（`main.py` 中已导入 `models.base` 来触发模型注册）。

### 4. 后端启动后访问 `http://localhost:8000/docs` 空白

- 检查控制台是否有错误输出。
- 尝试更换浏览器或清除缓存。

---

## 八、团队协作规范

- **分支管理**：开发时从 `main` 拉取新分支，完成后提交 PR 合并。
- **代码格式**：使用 PEP 8 规范，保持代码可读性。
- **每日站会**：每晚 9 点线上会议，同步进度和阻塞点。

---

如有任何问题，请在团队群中及时提出，我会协助解决。祝开发顺利！🚀
