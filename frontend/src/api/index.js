import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 自动带上 token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default api

// ========== 用户相关 API ==========
export const userApi = {
  register(data) {
    return api.post('/api/user/register', data)
  },
  login(data) {
    // 后端是 OAuth2PasswordRequestForm（x-www-form-urlencoded）
    const params = new URLSearchParams()
    params.append('username', data.username)
    params.append('password', data.password)
    return api.post('/api/user/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
  },
  getProfile() {
    return api.get('/api/user/profile')
  }
}

// ========== 新闻相关 API ==========
export const newsApi = {
  getNewsList(params) {
    return api.get('/api/news/', { params })
  },
  getNewsDetail(id) {
    return api.get(`/api/news/${id}`)
  },
  getRecommendations() {
    return api.get('/api/recommend/')
  }
}

// ========== 互动相关 API ==========
export const interactionApi = {
  likeArticle(articleId) {
    return api.post('/api/like', { article_id: articleId })
  },
  readArticle(articleId) {
    return api.post('/api/read', { article_id: articleId })
  }
}

// ========== 聊天相关 API ==========
export const chatApi = {
  /**
   * 会话式RAG对话：后端要求传入完整 messages 历史数组
   * @param {{role: 'user'|'assistant', content: string}[]} messages
   */
  sendMessages(messages) {
    return api.post('/api/chat', { messages })
  }
}
