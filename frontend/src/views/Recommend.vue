<template>
  <div class="recommend-page ina-page ina-page--narrow">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-info">
        <h2>⭐ 个性推荐</h2>
      </div>
      <el-button type="primary" :loading="refreshing" @click="loadRecommendations">
        <el-icon><Refresh /></el-icon>
        刷新推荐
      </el-button>
    </div>

    <!-- 用户偏好标签 -->
    <el-card class="preference-card" shadow="never">
      <div class="preference-header">
        <span>🎯 您的兴趣偏好</span>
        <el-tag size="small" type="info" effect="plain">基于点赞历史自动生成</el-tag>
      </div>
      <div class="preference-tags">
        <el-tag
          v-for="tag in userPreferences"
          :key="tag.name"
          :type="tag.type"
          effect="dark"
          size="large"
          round
          class="pref-tag"
        >
          {{ tag.name }}
          <span class="pref-score">{{ tag.score }}%</span>
        </el-tag>
      </div>
    </el-card>

    <!-- 推荐新闻列表 -->
    <div class="recommend-list">
      <div
        v-for="(news, index) in recommendedNews"
        :key="news.id"
        class="recommend-item"
      >
        <el-card shadow="hover" class="recommend-card" @click="$router.push(`/news/${news.id}`)">
          <div class="recommend-body">
            <div class="recommend-rank">
              <span :class="['rank-badge', `rank-${index + 1}`]">{{ index + 1 }}</span>
            </div>
            <div class="recommend-content">
              <div class="recommend-tags">
                <el-tag
                  v-for="tag in news.tags"
                  :key="tag"
                  size="small"
                  effect="light"
                  :style="getTagStyle(tag)"
                >
                  {{ tag }}
                </el-tag>
                <el-tag type="success" size="small" effect="plain" class="match-tag">
                  匹配度 {{ news.matchScore }}%
                </el-tag>
              </div>
              <h3 class="recommend-title">{{ news.title }}</h3>
              <p class="recommend-summary">{{ news.summary }}</p>
              <div class="recommend-footer">
                <span class="recommend-time">
                  <el-icon><Clock /></el-icon>
                  {{ news.time }}
                </span>
                <div class="recommend-actions" @click.stop>
                  <el-button
                    :type="news.liked ? 'danger' : 'default'"
                    size="small"
                    round
                    @click.stop="handleLike(news)"
                  >
                    <el-icon><component :is="news.liked ? 'StarFilled' : 'Star'" /></el-icon>
                    {{ news.liked ? '已点赞' : '点赞' }}
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty
      v-if="recommendedNews.length === 0 && !refreshing"
      description="暂无推荐数据，请先浏览和点赞一些新闻"
    >
      <el-button type="primary" @click="$router.push('/')">去看新闻</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Clock, Star, StarFilled } from '@element-plus/icons-vue'
import { newsApi, interactionApi } from '../api/index.js'
import api from '../api/index.js'

const refreshing = ref(false)

// 为8大分类分配完全不同的颜色（用于新闻卡片上的小标签）
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

// 用于顶部偏好 el-tag 的 type（保持 element-plus 风格）
const prefTagTypeMap = {
  '科技': '',
  '财经': 'warning',
  '体育': 'success',
  '娱乐': 'danger',
  '国际': 'info',
  '社会': 'warning',
  '教育': '',
  '健康': 'success'
}
const getPrefTagType = (tag) => prefTagTypeMap[tag] || 'info'

// 用户偏好
const userPreferences = ref([])
const recommendedNews = ref([])

const handleLike = async (news) => {
  const originLiked = news.liked
  news.liked = !news.liked
  try {
    if (news.liked) {
      await api.post('/api/like', { article_id: Number(news.id) })
    } else {
      await api.delete('/api/like', { data: { article_id: Number(news.id) } })
    }
    ElMessage.success(news.liked ? '已点赞 👍' : '已取消点赞')
  } catch (e) {
    console.warn('点赞请求失败', e)
    news.liked = originLiked
    ElMessage.error('操作失败，请先登录')
  }
}

const loadRecommendations = async () => {
  refreshing.value = true
  try {
    const res = await newsApi.getRecommendations()

    // 动态获取真实的用户偏好分布
    if (res && res.preferences) {
      userPreferences.value = res.preferences.map(pref => ({
        ...pref,
        type: getPrefTagType(pref.name)
      }))
    }

    // 获取点赞回显
    let likedSet = new Set()
    try {
      const likedRes = await api.get('/api/user/liked')
      if (likedRes && likedRes.data && likedRes.data.article_ids) {
        likedRes.data.article_ids.forEach(id => likedSet.add(id))
      }
    } catch(e) {}

    if (res && res.data && Array.isArray(res.data)) {
      recommendedNews.value = res.data.map(item => ({
        id: item.id,
        title: item.title,
        summary: item.summary || '无摘要',
        tags: item.tags ? item.tags.split(',') : ['未分类'],
        time: item.published_at ? item.published_at.substring(0, 16).replace('T', ' ') : '未知时间',
        matchScore: item.score ? Math.round(item.score * 100) : 80,
        liked: likedSet.has(item.id)
      }))
    } else {
      recommendedNews.value = []
      ElMessage.error(res.message || '获取推荐失败')
    }
  } catch (e) {
    console.error('获取个性推荐失败', e)
    const errorMsg = e.response?.data?.detail || e.message || '未知错误'
    ElMessage.error(`获取推荐失败: ${errorMsg}`)
    recommendedNews.value = []
  } finally {
    refreshing.value = false
  }
}

onMounted(() => {
  loadRecommendations()
})
</script>

<style scoped>
.recommend-page {
  padding-bottom: 32px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
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
.preference-card {
  margin-bottom: 32px;
  border-radius: var(--ina-radius-md);
  background: var(--ina-surface-solid);
  border: 1px solid var(--ina-border);
  box-shadow: var(--ina-shadow-sm);
}
.preference-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  font-size: 16px;
  font-weight: 600;
  color: var(--ina-text);
  letter-spacing: -0.2px;
}
.preference-tags {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.pref-tag {
  font-size: 14px;
  padding: 8px 18px;
  border: none;
  font-weight: 500;
}
.pref-score {
  margin-left: 6px;
  opacity: 0.8;
  font-size: 13px;
}
.recommend-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.recommend-card {
  border-radius: var(--ina-radius-md);
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid var(--ina-border);
}
.recommend-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--ina-shadow-hover);
  border-color: var(--ina-primary);
}
.recommend-body {
  display: flex;
  gap: 24px;
  align-items: flex-start;
  padding: 8px;
}
.recommend-rank {
  flex-shrink: 0;
}
.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--ina-radius-sm);
  font-size: 18px;
  font-weight: 700;
  color: var(--ina-text-2);
  background: var(--ina-bg-2);
  border: 1px solid var(--ina-border);
}
.rank-1 { background: var(--ina-accent); color: white; border-color: transparent; }
.rank-2 { background: var(--ina-success); color: white; border-color: transparent; }
.rank-3 { background: var(--ina-warning); color: white; border-color: transparent; }
.recommend-content {
  flex: 1;
  min-width: 0;
}
.recommend-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.match-tag {
  border-radius: var(--ina-radius-sm);
  font-weight: 600;
  letter-spacing: 0.5px;
}
.recommend-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--ina-text);
  margin: 0 0 10px;
  line-height: 1.4;
  letter-spacing: -0.3px;
}
.recommend-summary {
  font-size: 15px;
  color: var(--ina-text-2);
  line-height: 1.6;
  margin: 0 0 16px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.recommend-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.recommend-time {
  font-size: 12px;
  color: var(--ina-text-3);
  display: flex;
  align-items: center;
  gap: 4px;
}

@media (max-width: 768px) {
  .page-header {
    align-items: flex-start;
  }
}
</style>
