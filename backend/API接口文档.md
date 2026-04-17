# News API 接口文档

## 基础信息

- **基础URL**: `http://localhost:8000`（可根据实际部署调整）
- **接口前缀**: `/api/news`
- **数据格式**: JSON
- **字符编码**: UTF-8

## 通用响应格式

所有接口统一返回以下格式：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

- `code`: 状态码，0 表示成功，其他值表示失败
- `message`: 响应消息
- `data`: 业务数据（部分接口可能直接返回分页信息，不包含在 data 字段中）

---

## 1. 获取新闻列表

### 接口地址

```
GET /api/news/
```

### 请求参数（Query Parameters）

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| page | int | 否 | 页码，默认为 1，最小值为 1 | page=1 |
| size | int | 否 | 每页数量，默认为 10，范围 1-100 | size=10 |

### 请求示例

```bash
curl -X GET "http://localhost:8000/api/news/?page=1&size=10"
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "title": "新闻标题",
      "summary": "新闻摘要",
      "tags": "科技, AI",
      "published_at": "2026-03-27T10:00:00"
    }
  ],
  "total": 100,
  "page": 1,
  "size": 10
}
```

### 响应字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | int | 状态码，0 表示成功 |
| message | string | 响应消息 |
| data | array | 新闻列表数据 |
| data[].id | int | 新闻ID |
| data[].title | string | 新闻标题 |
| data[].summary | string | 新闻摘要 |
| data[].tags | string | 标签（逗号分隔） |
| data[].published_at | string | 发布时间（ISO 8601格式） |
| total | int | 总记录数 |
| page | int | 当前页码 |
| size | int | 每页数量 |

---

## 2. 获取新闻详情

### 接口地址

```
GET /api/news/{news_id}
```

### 路径参数（Path Parameters）

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| news_id | int | 是 | 新闻ID | 1 |

### 请求示例

```bash
curl -X GET "http://localhost:8000/api/news/1"
```

### 响应示例（成功）

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "title": "新闻标题",
    "content": "新闻详细内容...",
    "summary": "新闻摘要",
    "tags": "科技, AI",
    "source_url": "https://example.com/news/1",
    "published_at": "2026-03-27T10:00:00"
  }
}
```

### 响应示例（失败 - 新闻不存在）

```json
{
  "detail": "新闻不存在"
}
```

### 响应字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | int | 状态码，0 表示成功 |
| message | string | 响应消息 |
| data | object | 新闻详情数据 |
| data.id | int | 新闻ID |
| data.title | string | 新闻标题 |
| data.content | string | 新闻详细内容 |
| data.summary | string | 新闻摘要 |
| data.tags | string | 标签（逗号分隔） |
| data.source_url | string | 原文链接 |
| data.published_at | string | 发布时间（ISO 8601格式） |

---

## 3. 获取推荐新闻

### 接口地址

```
GET /api/recommend/
```

### 接口描述

根据用户历史行为智能推荐新闻。采用双策略推荐：
- **首次用户**（无点赞记录）：返回最近7天内最受欢迎的热门新闻
- **老用户**（有点赞记录）：基于向量相似度返回个性化推荐新闻

### 请求参数（Query Parameters）

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| limit | int | 否 | 返回新闻数量，默认为 10 | limit=10 |

### 请求示例

```bash
curl -X GET "http://localhost:8000/api/recommend/?limit=10"
```

### 响应示例（成功 - 热门新闻推荐）

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "title": "热门新闻标题",
      "summary": "新闻摘要",
      "tags": "科技, AI",
      "published_at": "2026-03-27T10:00:00"
    },
    {
      "id": 3,
      "title": "另一篇热门新闻",
      "summary": "新闻摘要",
      "tags": "经济, 财经",
      "published_at": "2026-03-26T15:30:00"
    }
  ],
  "strategy": "popular",
  "count": 2
}
```

### 响应示例（成功 - 个性化推荐）

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 5,
      "title": "基于你喜好的推荐",
      "summary": "新闻摘要",
      "tags": "科技, AI, 深度学习",
      "published_at": "2026-03-27T08:00:00"
    }
  ],
  "strategy": "personalized",
  "count": 1
}
```

### 响应字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | int | 状态码，0 表示成功 |
| message | string | 响应消息 |
| data | array | 推荐新闻列表 |
| data[].id | int | 新闻ID |
| data[].title | string | 新闻标题 |
| data[].summary | string | 新闻摘要 |
| data[].tags | string | 标签（逗号分隔） |
| data[].published_at | string | 发布时间（ISO 8601格式） |
| strategy | string | 推荐策略，`popular`（热门）或 `personalized`（个性化） |
| count | int | 返回的新闻数量 |

### 推荐策略说明

#### 策略1：热门推荐（popular）
- **触发条件**：用户无点赞记录（首次登录）
- **推荐逻辑**：返回最近7天内点赞数最高的新闻
- **排序**：按点赞数量降序排列

#### 策略2：个性化推荐（personalized）
- **触发条件**：用户有点赞记录（非首次登录）
- **推荐逻辑**：
  1. 获取用户点赞的所有新闻ID
  2. 计算这些新闻的向量平均值
  3. 基于平均向量在向量库中搜索相似新闻
  4. 过滤掉已点赞的新闻，返回最近的相似新闻
- **排序**：按发布时间降序排列（最新的优先）
- **降级策略**：如果个性化推荐结果不足，会用热门新闻补充

---

## 错误码说明

| HTTP状态码 | 说明 |
|-----------|------|
| 200 | 请求成功 |
| 404 | 资源不存在（如新闻ID不存在） |
| 422 | 请求参数验证失败 |
| 500 | 服务器内部错误 |

---

## 使用注意事项

1. **分页参数**: 列表接口建议使用分页，避免一次性返回过多数据
2. **时间格式**: 所有时间字段均使用 ISO 8601 格式
3. **标签格式**: tags 字段为逗号分隔的字符串，前端需要自行处理显示
4. **空值处理**: 某些字段可能为 null，前端需要做相应的空值判断
5. **CORS 配置**: 后端已配置跨域，默认允许 `http://localhost:5173`，可根据需要调整

---

## 前端调用示例

### JavaScript/Fetch

```javascript
// 获取新闻列表
async function getNewsList(page = 1, size = 10) {
  try {
    const response = await fetch(
      `http://localhost:8000/api/news/?page=${page}&size=${size}`
    );
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('获取新闻列表失败:', error);
    throw error;
  }
}

// 获取新闻详情
async function getNewsDetail(newsId) {
  try {
    const response = await fetch(
      `http://localhost:8000/api/news/${newsId}`
    );

    if (!response.ok) {
      throw new Error('新闻不存在');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('获取新闻详情失败:', error);
    throw error;
  }
}

// 获取推荐新闻
async function getRecommendations(limit = 10) {
  try {
    const response = await fetch(
      `http://localhost:8000/api/recommend/?limit=${limit}`
    );
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('获取推荐新闻失败:', error);
    throw error;
  }
}
```

### Axios

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000
});

// 获取新闻列表
export async function getNewsList(page = 1, size = 10) {
  const response = await api.get('/api/news/', {
    params: { page, size }
  });
  return response.data;
}

// 获取新闻详情
export async function getNewsDetail(newsId) {
  const response = await api.get(`/api/news/${newsId}`);
  return response.data;
}

// 获取推荐新闻
export async function getRecommendations(limit = 10) {
  const response = await api.get('/api/recommend/', {
    params: { limit }
  });
  return response.data;
}
```

---

## API 测试

后端服务启动后，可以通过以下方式测试接口：

1. **Swagger UI**: 访问 `http://localhost:8000/docs` 查看在线文档并进行测试
2. **ReDoc**: 访问 `http://localhost:8000/redoc` 查看更美观的文档
3. **Postman/cURL**: 使用工具进行接口测试

---

## 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2026-03-27 | 初始版本，包含新闻列表和详情接口 |
| 1.1.0 | 2026-03-27 | 新增推荐新闻接口，支持热门推荐和个性化推荐 |
