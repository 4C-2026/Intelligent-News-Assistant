<template>
  <div class="news-detail-page ina-page">
    <!-- 返回按钮 -->
    <div class="back-bar">
      <el-button text @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon>
        返回列表
      </el-button>
    </div>

    <div class="detail-layout">
      <!-- 左侧：新闻正文 -->
      <div class="article-section">
        <el-card class="article-card">
          <!-- 标签 -->
          <div class="article-tags">
            <el-tag
              v-for="tag in article.tags"
              :key="tag"
              size="small"
              effect="light"
              class="tag-item"
              :style="getTagStyle(tag)"
            >
              {{ tag }}
            </el-tag>
          </div>

          <!-- 标题 -->
          <h1 class="article-title">{{ article.title }}</h1>

          <!-- 元信息 -->
          <div class="article-meta">
            <span><el-icon><Clock /></el-icon> {{ article.time }}</span>
            <span><el-icon><View /></el-icon> {{ article.readCount }} 次阅读</span>
          </div>

          <!-- AI 摘要 -->
          <div class="ai-summary">
            <div class="ai-summary-header">
              <span>🤖 AI 智能摘要</span>
              <span class="ai-badge">RAG-ready</span>
            </div>
            <p>{{ article.summary }}</p>
          </div>
          
          <!-- 封面大图展示 -->
          <div v-if="article.coverImage" class="article-cover">
            <el-image 
              :src="article.coverImage" 
              fit="contain" 
              class="cover-img"
              :preview-src-list="[article.coverImage]"
            >
              <template #error>
                <div class="image-slot">
                  <el-icon><Picture /></el-icon>
                </div>
              </template>
            </el-image>
          </div>

          <!-- 正文 -->
          <div class="article-content">
            <p v-for="(p, idx) in article.paragraphs" :key="idx">{{ p }}</p>
          </div>

          <!-- 互动栏 -->
          <div class="article-actions">
            <el-button
              :type="article.liked ? 'danger' : 'default'"
              size="large"
              round
              @click="handleLike"
            >
              <el-icon><component :is="article.liked ? 'StarFilled' : 'Star'" /></el-icon>
              {{ article.liked ? '已点赞' : '点赞' }} ({{ article.likeCount }})
            </el-button>
            <el-button size="large" round @click="askAboutThisNews">
              <el-icon><ChatLineRound /></el-icon>
              针对此新闻提问
            </el-button>
          </div>
        </el-card>
      </div>

      <!-- 右侧：相关推荐 -->
      <div class="sidebar-section">
        <el-card class="sidebar-card">
          <template #header>
            <span class="sidebar-title">📌 相关推荐</span>
          </template>
          <div v-if="relatedNews.length > 0">
            <div
              v-for="item in relatedNews"
              :key="item.id"
              class="related-item"
              @click="navigateToNews(item.id)"
            >
              <h4>{{ item.title }}</h4>
              <p>{{ item.summary }}</p>
            </div>
          </div>
          <el-empty v-else description="暂无相关推荐" :image-size="60"></el-empty>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Clock, View, Star, StarFilled, ChatLineRound, Picture } from '@element-plus/icons-vue'
import { newsApi, interactionApi } from '../api/index.js'
import api from '../api/index.js'

const route = useRoute()
const router = useRouter()
const articleId = ref(route.params.id)

// 为8大分类分配完全不同的颜色
const tagColorMap = {
  '科技': { color: '#409EFF', bgColor: '#ecf5ff', borderColor: '#d9ecff' },
  '财经': { color: '#E6A23C', bgColor: '#fdf6ec', borderColor: '#faecd8' },
  '体育': { color: '#67C23A', bgColor: '#f0f9eb', borderColor: '#e1f3d8' },
  '娱乐': { color: '#F56C6C', bgColor: '#fef0f0', borderColor: '#fde2e2' },
  '国际': { color: '#909399', bgColor: '#f4f4f5', borderColor: '#e9e9eb' },
  '社会': { color: '#8e44ad', bgColor: '#f5eef8', borderColor: '#e8daef' },
  '教育': { color: '#00ced1', bgColor: '#e0ffff', borderColor: '#b0e0e6' },
  '健康': { color: '#ff69b4', bgColor: '#fff0f5', borderColor: '#ffb6c1' }
}

const getTagStyle = (tag) => {
  const t = tag.trim()
  if (tagColorMap[t]) {
    return {
      color: tagColorMap[t].color,
      backgroundColor: tagColorMap[t].bgColor,
      borderColor: tagColorMap[t].borderColor
    }
  }
  return {
    color: '#909399',
    backgroundColor: '#f4f4f5',
    borderColor: '#e9e9eb'
  }
}

const article = ref({
  id: articleId.value,
  title: '加载中...',
  summary: '',
  tags: [],
  coverImage: null,
  time: '',
  readCount: 0,
  liked: false,
  likeCount: 0,
  paragraphs: []
})

const relatedNews = ref([])

const navigateToNews = (id) => {
  router.push(`/news/${id}`)
}

const askAboutThisNews = () => {
  // 将文章ID和标题作为上下文参数传递给聊天页面
  router.push({
    path: '/chat',
    query: { 
      context_id: article.value.id,
      context_title: encodeURIComponent(article.value.title)
    }
  })
}

// 监听路由参数变化，切换新闻时重新加载
watch(() => route.params.id, (newId) => {
  if (newId) {
    window.location.reload()
  }
})

const handleLike = async () => {
  const originLiked = article.value.liked
  article.value.liked = !article.value.liked
  // 防止 likeCount 变为负数
  if (article.value.liked) {
    article.value.likeCount += 1
  } else {
    article.value.likeCount = Math.max(0, article.value.likeCount - 1)
  }

  try {
    if (article.value.liked) {
      await api.post('/api/like', { article_id: Number(article.value.id) })
    } else {
      await api.delete('/api/like', { data: { article_id: Number(article.value.id) } })
    }
    ElMessage.success(article.value.liked ? '已点赞 👍' : '已取消点赞')
  } catch (e) {
    console.warn('点赞请求失败', e)
    // 失败则回滚
    article.value.liked = originLiked
    if (article.value.liked) {
      article.value.likeCount += 1
    } else {
      article.value.likeCount = Math.max(0, article.value.likeCount - 1)
    }
    ElMessage.error('操作失败，请先登录')
  }
}

onMounted(async () => {
  try {
    // 1. 获取新闻详情（后端同时返回相关推荐 related 字段）
    const res = await newsApi.getNewsDetail(articleId.value)

    // 2. 获取点赞状态回显
    let isLiked = false
    try {
      const likedRes = await api.get('/api/user/liked')
      if (likedRes && likedRes.data && likedRes.data.article_ids) {
        isLiked = likedRes.data.article_ids.includes(Number(articleId.value))
      }
    } catch(e) {}

    if (res && res.data) {
      const data = res.data
      article.value = {
        id: data.id,
        title: data.title,
        summary: data.summary || '暂无摘要',
        tags: data.tags ? data.tags.split(',') : ['未分类'],
        coverImage: data.cover_image || null,
        time: data.published_at ? data.published_at.substring(0, 16).replace('T', ' ') : '未知时间',
        readCount: data.read_count || 0,
        liked: isLiked,
        likeCount: data.like_count || 0,
        paragraphs: data.content ? data.content.split('\n').filter(p => p.trim()) : ['正文加载失败，或者内容为空。']
      }

      // 3. 更新右侧相关推荐（来自后端向量检索）
      if (data.related && Array.isArray(data.related)) {
        relatedNews.value = data.related
      } else {
        relatedNews.value = []
      }
    }
  } catch (e) {
    console.error('获取文章详情失败', e)
    ElMessage.error('获取文章详情失败')
  }

  try {
    await interactionApi.readArticle(articleId.value)
  } catch (e) {
    // 静默处理，可能用户没登录
  }
})
</script>

<style scoped>
.news-detail-page {
  padding-bottom: 24px;
  max-width: 1600px; /* 进一步放宽整个页面 */
  width: 100%;
  margin: 0 auto;
}
.back-bar {
  margin-bottom: 20px;
}
.detail-layout {
  display: flex;
  gap: 40px;
  align-items: flex-start;
}
.article-section {
  flex: 1; /* 正文占据所有剩余空间 */
  min-width: 0;
}
.sidebar-section {
  width: 280px; /* 显著缩小侧边栏宽度，让出更多空间给正文 */
  flex-shrink: 0;
}
.article-card {
  padding: 40px 60px;
}
:deep(.article-card.el-card) {
  border: none;
  border-radius: var(--ina-radius-lg);
}
.article-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.tag-item {
  border-radius: var(--ina-radius-sm);
  font-weight: 500;
  border: none;
}
.article-title {
  font-size: 32px;
  font-weight: 800;
  color: var(--ina-text);
  line-height: 1.3;
  margin: 0 0 24px;
  letter-spacing: -0.5px;
}
.article-meta {
  display: flex;
  gap: 24px;
  font-size: 14px;
  color: var(--ina-text-3);
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--ina-border);
}
.article-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}
.ai-summary {
  background: var(--ina-bg-2);
  border-left: 4px solid var(--ina-accent);
  border-radius: 0 var(--ina-radius-sm) var(--ina-radius-sm) 0;
  padding: 24px;
  margin-bottom: 32px;
}
.ai-summary-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 15px;
  font-weight: 700;
  color: var(--ina-accent);
  margin-bottom: 12px;
  letter-spacing: -0.3px;
}
.ai-badge {
  font-size: 12px;
  font-weight: 700;
  color: var(--ina-surface-solid);
  background: var(--ina-accent);
  padding: 4px 10px;
  border-radius: var(--ina-radius-sm);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.ai-summary p {
  margin: 0;
  font-size: 16px;
  color: var(--ina-text-2);
  line-height: 1.7;
}
.article-cover {
  margin: 0 0 32px;
  width: 100%;
  border-radius: var(--ina-radius-sm);
  overflow: hidden;
  display: flex;
  justify-content: center;
  background: var(--ina-bg);
}
.article-cover .cover-img {
  max-height: 500px;
  width: auto;
  max-width: 100%;
  border-radius: var(--ina-radius-sm);
}
.article-cover .image-slot {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  min-height: 200px;
  background: var(--ina-bg);
  color: var(--ina-text-3);
  font-size: 32px;
}
.article-content p {
  font-size: 18px;
  line-height: 1.8;
  color: var(--ina-text);
  margin: 0 0 24px;
  letter-spacing: 0.2px;
}
.article-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  padding-top: 32px;
  margin-top: 40px;
  border-top: 1px solid var(--ina-border);
}
.sidebar-card {
  border-radius: var(--ina-radius-md);
  position: sticky;
  top: 84px;
  border: none;
}
:deep(.sidebar-card.el-card) {
  border: none;
}
.sidebar-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--ina-text);
}
.related-item {
  padding: 12px 0;
  border-bottom: 1px solid rgba(31, 45, 61, 0.08);
  cursor: pointer;
  transition: all 0.2s;
}
.related-item:last-child {
  border-bottom: none;
}
.related-item:hover {
  padding-left: 8px;
}
.related-item:hover h4 {
  color: var(--ina-primary);
}
.related-item h4 {
  font-size: 15px;
  font-weight: 600;
  color: var(--ina-text);
  margin: 0 0 8px;
  line-height: 1.4;
  transition: color 0.2s;
}
.related-item p {
  font-size: 13px;
  color: var(--ina-text-2);
  margin: 0;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .detail-layout {
    flex-direction: column;
  }
  .sidebar-section {
    width: 100%;
  }
  .article-actions {
    flex-wrap: wrap;
  }
}
</style>
