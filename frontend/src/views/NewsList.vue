<template>
  <div class="news-list-page ina-page">
    <!-- 页面标题栏 -->
    <div class="page-header">
      <div class="header-info">
        <h2>📋 新闻列表</h2>
        <p>实时采集，AI 智能分析摘要与标签</p>
      </div>
      <div class="header-actions">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索新闻..."
          prefix-icon="Search"
          clearable
          style="width: 260px"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>搜索
        </el-button>
        <el-button type="success" plain @click="refreshNews" :loading="isRefreshing">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
    </div>

    <!-- 分类标签筛选 -->
    <div class="tag-filter">
      <span class="filter-label">分类筛选：</span>
      <el-check-tag
        v-for="tag in allTags"
        :key="tag"
        :checked="selectedTag === tag"
        @change="handleTagFilter(tag)"
        class="filter-tag"
      >
        {{ tag }}
      </el-check-tag>
    </div>

    <!-- 新闻卡片列表 -->
    <div class="news-grid">
      <el-card
        v-for="news in displayedNews"
        :key="news.id"
        class="news-card"
        shadow="hover"
        @click="goToDetail(news.id)"
      >
        <div class="news-card-body">
          <div class="news-cover" v-if="news.coverImage">
            <el-image 
              :src="news.coverImage" 
              fit="cover" 
              class="cover-img"
              loading="lazy"
            >
              <template #error>
                <div class="image-slot">
                  <el-icon><Picture /></el-icon>
                </div>
              </template>
            </el-image>
          </div>
          <div class="news-content-wrapper">
            <div class="news-meta">
              <el-tag
              v-for="tag in news.tags"
              :key="tag"
              size="small"
              effect="light"
              class="news-tag"
              :style="getTagStyle(tag)"
            >
              {{ tag }}
            </el-tag>
          </div>
          <h3 class="news-title">{{ news.title }}</h3>
          <p class="news-summary">{{ news.summary }}</p>
          <div class="news-footer">
            <span class="news-time">
              <el-icon><Clock /></el-icon>
              {{ news.time }}
            </span>
            <div class="news-actions" @click.stop>
              <el-button
                :type="news.liked ? 'danger' : 'default'"
                size="small"
                round
                @click.stop="handleLike(news)"
              >
                <el-icon><component :is="news.liked ? 'StarFilled' : 'Star'" /></el-icon>
                {{ news.liked ? '已点赞' : '点赞' }}
                <span v-if="news.likeCount" class="like-count">{{ news.likeCount }}</span>
              </el-button>
              <el-button size="small" round @click.stop="goToDetail(news.id)">
                <el-icon><View /></el-icon>
                阅读
              </el-button>
            </div>
          </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 空状态 -->
    <el-empty v-if="displayedNews.length === 0" description="暂无更多新闻" />

    <!-- 分页 -->
    <div class="pagination-wrapper" v-if="displayedNews.length > 0">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="filteredNews.length"
        layout="prev, pager, next, total"
        background
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Clock, Star, StarFilled, View, Refresh, Picture } from '@element-plus/icons-vue'
import { newsApi, interactionApi } from '../api/index.js'
import api from '../api/index.js'

const router = useRouter()
const searchKeyword = ref('')
const selectedTag = ref('全部')
const currentPage = ref(1)
const pageSize = 9

const allTags = ['全部', '科技', '财经', '体育', '娱乐', '国际', '社会', '教育', '健康']

const newsList = ref([])
const isRefreshing = ref(false)

// 定义组件名称以便 keep-alive 能够正确匹配
defineOptions({
  name: 'NewsList'
})

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

const filteredNews = computed(() => {
  let result = newsList.value
  if (selectedTag.value !== '全部') {
    result = result.filter(n => n.tags.includes(selectedTag.value))
  }
  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase()
    result = result.filter(n =>
      n.title.toLowerCase().includes(kw) || n.summary.toLowerCase().includes(kw)
    )
  }
  return result
})

const displayedNews = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredNews.value.slice(start, start + pageSize)
})

const handleSearch = () => {
  currentPage.value = 1
}

const handleTagFilter = (tag) => {
  selectedTag.value = selectedTag.value === tag ? '全部' : tag
  currentPage.value = 1
}

const handleLike = async (news) => {
  const originLiked = news.liked
  news.liked = !news.liked
  // 防止 likeCount 变成负数
  if (news.liked) {
    news.likeCount += 1
  } else {
    news.likeCount = Math.max(0, news.likeCount - 1)
  }

  try {
    if (news.liked) {
      await api.post('/api/like', { article_id: Number(news.id) })
    } else {
      await api.delete('/api/like', { data: { article_id: Number(news.id) } })
    }
    ElMessage.success(news.liked ? '已点赞 👍' : '已取消点赞')
  } catch (e) {
    console.warn('点赞请求失败', e)
    // 失败则回滚
    news.liked = originLiked
    if (news.liked) {
      news.likeCount += 1
    } else {
      news.likeCount = Math.max(0, news.likeCount - 1)
    }
    ElMessage.error('操作失败，请先登录')
  }
}

const goToDetail = (id) => {
  router.push(`/news/${id}`)
}

const loadNewsList = async (showToast = false) => {
  try {
    if (showToast) {
      isRefreshing.value = true
    }
    // 1. 获取新闻列表 (由于后台自动爬取可能产生更多新闻，可以增加获取数量或保持50，具体视需求而定)
    // 获取更多数据，比如最近 100 条，确保能看到最新的新闻
    const res = await newsApi.getNewsList({ page: 1, size: 100 })

    // 2. 获取用户点赞列表，用于回显状态
    let likedSet = new Set()
    try {
      const likedRes = await api.get('/api/user/liked')
      if (likedRes && likedRes.data && likedRes.data.article_ids) {
        likedRes.data.article_ids.forEach(id => likedSet.add(id))
      }
    } catch (e) {
      console.warn('无法获取用户点赞列表', e)
    }

    if (res && res.data && Array.isArray(res.data)) {
      // 适配后端返回的字段
      newsList.value = res.data.map(item => ({
        id: item.id,
        title: item.title,
        summary: item.summary || '无摘要',
        tags: item.tags ? item.tags.split(',') : ['未分类'],
        coverImage: item.cover_image || null,
        time: item.published_at ? item.published_at.substring(0, 16).replace('T', ' ') : '未知时间',
        liked: likedSet.has(item.id),
        likeCount: item.like_count || 0
      }))
      
      if (showToast) {
        ElMessage.success('新闻已更新')
      }
    }
  } catch (e) {
    console.error('获取新闻列表失败', e)
    if (showToast) {
      ElMessage.error('获取新闻列表失败')
    }
  } finally {
    isRefreshing.value = false
  }
}

const refreshNews = () => {
  // 手动点击刷新时，回到第一页并显示提示
  currentPage.value = 1
  loadNewsList(true)
}

onMounted(() => {
  // 初次加载
  loadNewsList()
  
  // 设置定时器，每 5 分钟 (300000 毫秒) 自动刷新一次新闻列表
  const refreshInterval = setInterval(() => {
    loadNewsList()
  }, 300000)

  // 避免内存泄漏，可以在需要的时候清理（不过在这个顶层路由一般不需要，如果严格的话应该使用 onUnmounted）
})

// 当组件从缓存中被激活时（例如从详情页返回）
onActivated(() => {
  // 这里可以选择是否静默刷新列表，或者保持原样。
  // 为了确保点赞状态等可能是最新的，可以在后台静默刷新，但不改变页码
  // loadNewsList() // 暂时注释掉避免突然刷新导致阅读中断
})
</script>

<style scoped>
.news-list-page {
  padding-bottom: 24px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}
.header-info h2 {
  font-size: 24px;
  font-weight: 700;
  color: var(--ina-text);
  margin: 0 0 4px;
  letter-spacing: -0.5px;
}
.header-info p {
  font-size: 14px;
  color: var(--ina-text-2);
  margin: 0;
}
.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.tag-filter {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 24px;
  flex-wrap: wrap;
  background: var(--ina-surface-solid);
  padding: 16px;
  border-radius: var(--ina-radius-md);
  border: 1px solid var(--ina-border);
  box-shadow: var(--ina-shadow-sm);
}
.filter-label {
  font-size: 14px;
  color: var(--ina-text-2);
  font-weight: 600;
}
.filter-tag {
  cursor: pointer;
  border-radius: var(--ina-radius-sm);
  transition: all 0.2s ease;
  padding: 6px 16px;
  font-size: 14px;
  font-weight: 500;
  border: 1px solid transparent;
}
.filter-tag.is-checked {
  background-color: var(--ina-primary) !important;
  color: white !important;
}
.filter-tag:hover:not(.is-checked) {
  background-color: var(--ina-bg-2);
}
.news-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}
.news-card {
  cursor: pointer;
  border-radius: var(--ina-radius-md);
  transition: all 0.3s ease;
  border: 1px solid var(--ina-border);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.news-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--ina-shadow-hover);
  border-color: var(--ina-primary);
}
.news-card-body {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.news-cover {
  width: 100%;
  height: 160px;
  overflow: hidden;
  border-bottom: 1px solid var(--ina-border);
}
.cover-img {
  width: 100%;
  height: 100%;
  transition: transform 0.3s ease;
}
.news-card:hover .cover-img {
  transform: scale(1.05);
}
.image-slot {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  background: var(--ina-surface);
  color: var(--ina-text-3);
  font-size: 24px;
}
.news-content-wrapper {
  padding: 20px;
  display: flex;
  flex-direction: column;
  flex: 1;
  background: var(--ina-surface-solid);
}
.news-meta {
  display: flex;
  gap: 6px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.news-tag {
  border-radius: var(--ina-radius-sm);
  font-weight: 500;
  border: none;
}
.news-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--ina-text);
  margin: 0 0 12px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  letter-spacing: -0.3px;
}
.news-summary {
  font-size: 14px;
  color: var(--ina-text-2);
  line-height: 1.6;
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin: 0 0 20px;
}
.news-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid var(--ina-border);
}
.news-time {
  font-size: 12px;
  color: var(--ina-text-3);
  display: flex;
  align-items: center;
  gap: 4px;
}
.news-actions {
  display: flex;
  gap: 8px;
}
.like-count {
  margin-left: 2px;
}
.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

@media (max-width: 768px) {
  .header-actions {
    width: 100%;
  }
  .header-actions :deep(.el-input) {
    flex: 1;
  }
}
/* 当卡片原本有内边距时，去掉以适应通栏图片 */
:deep(.el-card__body) {
  padding: 0;
}
.news-meta {
  margin-bottom: 12px;
}
</style>
