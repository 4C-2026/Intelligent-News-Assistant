# 会话RAG对话接口文档

## 概述

基于检索增强生成（RAG）的智能新闻问答系统接口，提供**会话式**新闻问答功能，支持多轮上下文对话和查询重构。

## 接口规范

### 基础信息
- **基础URL**: `http://localhost:8000`（可根据实际部署调整）
- **接口前缀**: `/api`
- **数据格式**: JSON
- **字符编码**: UTF-8

### 通用响应格式
所有接口统一返回以下格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

**字段说明**:
- `code`: 状态码，0表示成功，其他值表示失败
- `message`: 响应消息
- `data`: 业务数据

## 会话RAG对话接口

### 接口信息
- **请求方法**: POST
- **接口路径**: `/api/chat`
- **前端传入参数**: `messages` 数组（完整的对话历史）
- **无登录验证**: 不需要从token解析user_id，不需要任何登录验证
- **会话支持**: 支持多轮上下文对话，理解省略式提问（如"乌克兰呢？"）

### 请求示例
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "俄罗斯和乌克兰的冲突有什么最新进展？"},
      {"role": "assistant", "content": "根据相关新闻，俄罗斯和乌克兰的冲突在多个战线都有新动态..."},
      {"role": "user", "content": "乌克兰呢？"}
    ]
  }'
```

### 请求参数
```json
{
  "messages": [
    {
      "role": "string, 必填, 取值: 'user' 或 'assistant'",
      "content": "string, 必填, 消息内容"
    }
  ]
}
```

**字段说明**:
- `messages`: 完整的对话历史消息数组
  - 最后一条消息必须是用户消息（`role: "user"`）
  - 消息按时间顺序排列
  - 前端负责维护会话历史，关闭页面即消失

### 成功响应示例
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "answer": "根据相关新闻内容，乌克兰在俄乌冲突中的最新情况是..."
  }
}
```

### 错误响应示例

#### 空消息数组
```json
{
  "code": 400,
  "message": "对话历史不能为空",
  "data": {
    "answer": ""
  }
}
```

#### 最后一条消息不是用户消息
```json
{
  "code": 400,
  "message": "最后一条消息必须是用户消息",
  "data": {
    "answer": ""
  }
}
```

#### 空问题
```json
{
  "code": 400,
  "message": "用户问题不能为空",
  "data": {
    "answer": ""
  }
}
```

#### API频率限制
```json
{
  "code": 429,
  "message": "API调用频率限制，请稍后重试",
  "data": {
    "answer": ""
  }
}
```

#### API认证失败
```json
{
  "code": 401,
  "message": "API认证失败，请检查API密钥",
  "data": {
    "answer": ""
  }
}
```

#### 服务器内部错误
```json
{
  "code": 500,
  "message": "会话RAG处理失败: [具体错误信息]",
  "data": {
    "answer": ""
  }
}
```

## 健康检查接口

### 接口信息
- **请求方法**: GET
- **接口路径**: `/api/chat/health`

### 请求示例
```bash
curl "http://localhost:8000/api/chat/health"
```

### 响应示例
```json
{
  "code": 0,
  "message": "RAG服务运行正常",
  "data": {
    "status": "healthy"
  }
}
```

## 根路径接口

### 接口信息
- **请求方法**: GET
- **接口路径**: `/`

### 请求示例
```bash
curl "http://localhost:8000/"
```

### 响应示例
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "service": "智能新闻助手API",
    "version": "1.0.0",
    "status": "running",
    "endpoints": {
      "chat": "/api/chat",
      "health": "/api/chat/health",
      "docs": "/docs",
      "redoc": "/redoc"
    }
  }
}
```

## API文档

### 交互式文档
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## 开发环境配置

### 1. 进入backend目录
```bash
cd backend
```

### 2. 激活Python虚拟环境
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. 安装依赖
确保已安装以下依赖：
- `fastapi==0.104.1`
- `uvicorn`
- 其他项目依赖

### 4. 启动服务器
```bash
python main.py
```

或者直接使用uvicorn：
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 项目结构

```
backend/
├── main.py                    # FastAPI主应用
├── routers/
│   └── chat.py               # 会话RAG对话接口路由
├── services/
│   ├── session_rag_service.py # 会话RAG核心服务（新增）
│   ├── rag_service.py        # 原始RAG核心服务（保留）
│   ├── embedding_service.py  # 向量化服务
│   ├── vector_store.py       # 向量数据库操作
│   └── llm_service.py        # 大模型服务
├── models/                   # 数据模型
├── database.py               # 数据库配置
└── .env                      # 环境变量配置
```

**新增文件说明**:
- `session_rag_service.py`: 会话RAG核心服务，支持多轮对话和查询重构
- 更新 `chat.py`: 改为使用会话RAG服务，接口参数从 `message` 改为 `messages` 数组

## 技术栈

### 后端框架
- **FastAPI**: 高性能Web框架，支持异步请求处理
- **Pydantic**: 数据验证和序列化

### RAG核心
- **智谱AI API**: 用于大模型调用
- **ChromaDB**: 向量数据库，用于新闻向量存储和检索
- **Sentence Transformers**: 文本向量化

### 数据库
- **SQLite**: 关系型数据库，存储新闻内容
- **SQLAlchemy**: ORM框架

## 会话RAG工作原理

### 1. 查询重构
- **输入**: 完整的对话历史（messages数组）
- **处理**: 使用GLM-4-Flash大模型重构查询语句
- **输出**: 完整、清晰、可直接检索的查询语句
- **示例**: "乌克兰呢？" → "乌克兰在俄乌冲突中的最新情况和地位"

### 2. 向量检索
- **步骤1**: 将重构后的查询进行向量化
- **步骤2**: 在向量数据库中检索最相关的新闻ID
- **步骤3**: 根据新闻ID从数据库获取新闻正文

### 3. 答案生成
- **输入**: 对话历史 + 检索到的新闻内容 + 当前问题
- **处理**: 调用GLM-4-Flash生成连贯、准确的答案
- **输出**: 基于新闻内容和对话上下文的最终答案

## 接口特点

### 1. 会话式接口设计
- **多轮对话**: 支持完整的对话历史传递
- **上下文理解**: 理解省略式、指代式提问
- **查询重构**: 自动将不完整查询重构为完整查询

### 2. 前端会话管理
- **历史维护**: 前端在内存中维护会话历史
- **会话生命周期**: 从打开网站到关闭网站为一轮连续会话
- **无状态后端**: 后端不存储会话状态，每次请求包含完整历史

### 3. 完整的错误处理
- **输入验证错误**（400）: 空消息数组、最后消息非用户、空问题
- **API频率限制错误**（429）: 智谱API调用频率限制
- **认证错误**（401）: API密钥认证失败
- **超时错误**（504）: API请求超时
- **服务器内部错误**（500）: 向量化、检索或模型调用失败

### 4. 健康监控
- **服务健康检查接口**: 检查会话RAG服务可用性
- **API连接测试**: 测试智谱API连接状态
- **详细状态信息**: 服务运行状态和版本信息

## 使用示例

### 示例1: 单轮对话
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "人工智能有什么最新进展？"}
    ]
  }'
```

### 示例2: 多轮对话（省略式提问）
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "俄罗斯和乌克兰的冲突有什么最新进展？"},
      {"role": "assistant", "content": "根据相关新闻，俄罗斯和乌克兰的冲突在多个战线都有新动态..."},
      {"role": "user", "content": "乌克兰呢？"}
    ]
  }'
```

### 示例3: 技术话题深入
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "特斯拉发布了什么新产品？"},
      {"role": "assistant", "content": "特斯拉最近发布了新款Model 3..."},
      {"role": "user", "content": "它的电池技术有什么改进？"},
      {"role": "assistant", "content": "新款Model 3采用了更高效的电池组..."},
      {"role": "user", "content": "自动驾驶功能有更新吗？"}
    ]
  }'
```

## 测试方法

### 1. 单元测试
```bash
# 测试会话RAG API
python test_session_chat_api.py

# 测试示例使用
python example_session_chat_api_usage.py
```

### 2. 手动测试
使用curl或Postman测试接口：

#### 测试单轮对话
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "人工智能有什么最新进展？"}
    ]
  }'
```

#### 测试多轮对话
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "特斯拉发布了什么新产品？"},
      {"role": "assistant", "content": "测试回答..."},
      {"role": "user", "content": "电池技术呢？"}
    ]
  }'
```

#### 测试健康检查
```bash
curl "http://localhost:8000/api/chat/health"
```

#### 测试根路径
```bash
curl "http://localhost:8000/"
```

### 3. 查看API文档
访问 `http://localhost:8000/docs` 查看交互式API文档。

## 前端集成指南

### 1. 会话管理
```javascript
// 前端会话管理示例
class ChatSession {
  constructor() {
    this.messages = []; // 存储对话历史
  }
  
  // 添加用户消息
  addUserMessage(content) {
    this.messages.push({ role: "user", content });
  }
  
  // 添加助手消息
  addAssistantMessage(content) {
    this.messages.push({ role: "assistant", content });
  }
  
  // 发送请求
  async sendMessage(userInput) {
    // 添加用户消息
    this.addUserMessage(userInput);
    
    // 准备请求数据
    const requestData = {
      messages: this.messages
    };
    
    try {
      // 发送请求
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(requestData)
      });
      
      const result = await response.json();
      
      if (result.code === 0) {
        // 添加助手回答到会话历史
        this.addAssistantMessage(result.data.answer);
        return result.data.answer;
      } else {
        throw new Error(result.message);
      }
    } catch (error) {
      // 移除失败的用户消息
      this.messages.pop();
      throw error;
    }
  }
  
  // 清空会话
  clear() {
    this.messages = [];
  }
}
```

### 2. 错误处理
```javascript
// 前端错误处理示例
async function handleChatRequest(messages) {
  try {
    const response = await fetch("http://localhost:8000/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages })
    });
    
    const result = await response.json();
    
    switch (result.code) {
      case 0:
        return result.data.answer;
      case 400:
        throw new Error(`输入错误: ${result.message}`);
      case 401:
        throw new Error("API认证失败，请检查配置");
      case 429:
        throw new Error("请求过于频繁，请稍后重试");
      case 500:
        throw new Error(`服务器错误: ${result.message}`);
      case 504:
        throw new Error("请求超时，请检查网络连接");
      default:
        throw new Error(`未知错误: ${result.message}`);
    }
  } catch (error) {
    if (error.name === "TypeError" && error.message.includes("fetch")) {
      throw new Error("网络连接失败，请检查服务器状态");
    }
    throw error;
  }
}
```

### 3. 会话生命周期
- **开始**: 用户打开网站，初始化空会话
- **进行**: 用户提问，前端维护对话历史
- **结束**: 用户关闭网站，会话历史消失
- **新会话**: 重新打开网站，开始新的会话

## 注意事项

### 1. 环境变量配置
确保在 `.env` 文件中配置正确的API密钥：
```
ZHIPU_API_KEY=your_api_key_here
```

### 2. 数据库初始化
在首次使用前，需要：
1. 创建SQLite数据库表
2. 导入新闻数据
3. 初始化向量数据库

### 3. 性能考虑
- RAG处理需要时间（通常2-5秒）
- 向量检索性能取决于新闻数量
- API调用有频率限制

### 4. 错误处理
前端应处理以下情况：
- 网络超时
- API频率限制
- 服务器错误
- 空响应

## 扩展功能

### 未来可扩展的接口
1. **批量问答接口**: 支持多个问题同时处理
2. **历史记录接口**: 保存用户问答历史
3. **反馈接口**: 用户对答案的反馈
4. **新闻推荐接口**: 基于用户问题的新闻推荐

### 性能优化
1. **缓存机制**: 缓存常见问题的答案
2. **异步处理**: 长时间任务异步处理
3. **分页检索**: 大量新闻时的分页检索

## 技术支持

如有问题，请检查：
1. 服务器是否正常运行
2. API密钥是否正确配置
3. 数据库连接是否正常
4. 网络连接是否通畅

## 版本历史

### v2.0.0 (2024-03-31)
- **会话RAG升级**: 支持多轮上下文对话
- **查询重构**: 使用GLM-4-Flash重构省略式查询
- **接口变更**: 请求参数从 `message` 改为 `messages` 数组
- **新增服务**: `session_rag_service.py` 会话RAG核心服务
- **前端集成**: 提供完整的前端会话管理示例

### v1.0.0 (2024-03-30)
- 初始版本发布
- 实现基本的RAG对话接口
- 支持新闻问答功能
- 完整的错误处理和健康检查
