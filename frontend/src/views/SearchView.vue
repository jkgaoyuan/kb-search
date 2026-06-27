<template>
  <div class="search-view">
    <!-- 搜索框区域 -->
    <div class="search-box-area">
      <el-input
        v-model="searchQuery"
        placeholder="搜索知识库..."
        size="large"
        clearable
        @keyup.enter="handleSearch"
        class="search-input"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
        <template #append>
          <el-button type="primary" @click="handleSearch">
            搜索
          </el-button>
        </template>
      </el-input>

      <!-- 搜索建议 -->
      <div v-if="suggestions.length > 0" class="suggestions">
        <div
          v-for="s in suggestions"
          :key="s"
          class="suggestion-item"
          @click="searchQuery = s; handleSearch()"
        >
          <el-icon><Search /></el-icon>
          <span>{{ s }}</span>
        </div>
      </div>
    </div>

    <!-- 热门搜索 -->
    <div class="hot-searches" v-if="!hasSearched">
      <h3><el-icon><TrendCharts /></el-icon> 热门搜索</h3>
      <div class="hot-tags">
        <el-tag
          v-for="(item, index) in hotSearches"
          :key="index"
          :type="index < 3 ? 'danger' : ''"
          effect="plain"
          class="hot-tag"
          @click="searchQuery = item.query; handleSearch()"
        >
          <span class="hot-rank">{{ index + 1 }}</span>
          {{ item.query }}
          <span class="hot-count">({{ item.count }})</span>
        </el-tag>
      </div>
    </div>

    <!-- 搜索结果 -->
    <div v-if="hasSearched" class="search-results">
      <div class="results-header">
        <span>找到 {{ total }} 条结果</span>
        <el-radio-group v-model="sortBy" size="small" @change="handleSearch">
          <el-radio-button label="relevance">相关度</el-radio-button>
          <el-radio-button label="updated_at">更新时间</el-radio-button>
          <el-radio-button label="view_count">浏览量</el-radio-button>
        </el-radio-group>
      </div>

      <div v-if="loading" class="loading-state">
        <el-skeleton :rows="5" animated />
      </div>

      <div v-else-if="results.length === 0" class="empty-state">
        <el-empty description="未找到相关文档" />
      </div>

      <div v-else class="result-list">
        <div
          v-for="item in results"
          :key="item.id"
          class="result-item"
          @click="goToDetail(item.id)"
        >
          <div class="result-title" v-html="item.title_highlighted || item.title"></div>
          <div class="result-summary" v-html="item.content_highlighted"></div>
          <div class="result-meta">
            <el-tag size="small" type="info">{{ item.file_type }}</el-tag>
            <span class="meta-item">
              <el-icon><View /></el-icon>
              {{ item.view_count }}
            </span>
            <span class="meta-item">
              <el-icon><Timer /></el-icon>
              {{ formatDate(item.updated_at) }}
            </span>
            <span class="meta-item relevance">
              相关度: {{ (item.relevance_score * 100).toFixed(1) }}%
            </span>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <el-pagination
        v-if="total > pageSize"
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="handleSearch"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { searchDocuments, getSearchSuggestions, getHotSearches } from '@/api/search'
import { debounce } from '@/utils/common'

const router = useRouter()

const searchQuery = ref('')
const sortBy = ref('relevance')
const page = ref(1)
const pageSize = ref(20)
const results = ref([])
const total = ref(0)
const loading = ref(false)
const hasSearched = ref(false)
const suggestions = ref([])
const hotSearches = ref([])

// 加载热门搜索
const loadHotSearches = async () => {
  try {
    const res = await getHotSearches({ limit: 10 })
    hotSearches.value = res.searches || []
  } catch (e) {
    console.error(e)
  }
}

loadHotSearches()

// 搜索建议（防抖）
const fetchSuggestions = debounce(async (query) => {
  if (!query || query.length < 2) {
    suggestions.value = []
    return
  }
  try {
    const res = await getSearchSuggestions(query)
    suggestions.value = res.suggestions || []
  } catch (e) {
    suggestions.value = []
  }
}, 300)

watch(searchQuery, (val) => {
  fetchSuggestions(val)
})

// 执行搜索
const handleSearch = async () => {
  if (!searchQuery.value.trim()) return

  hasSearched.value = true
  loading.value = true
  suggestions.value = []

  try {
    const res = await searchDocuments({
      q: searchQuery.value,
      sort: sortBy.value,
      page: page.value,
      page_size: pageSize.value
    })
    results.value = res.results || []
    total.value = res.total || 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const goToDetail = (id) => {
  router.push(`/document/${id}`)
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.search-view {
  max-width: 900px;
  margin: 0 auto;
}

.search-box-area {
  position: relative;
  margin-bottom: 30px;
}

.search-input {
  width: 100%;
}

.search-input :deep(.el-input__inner) {
  height: 50px;
  font-size: 16px;
}

.suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  z-index: 100;
  padding: 8px 0;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  cursor: pointer;
  color: #606266;
}

.suggestion-item:hover {
  background: #f5f7fa;
  color: #409EFF;
}

.hot-searches {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
}

.hot-searches h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 15px;
  color: #303133;
}

.hot-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.hot-tag {
  cursor: pointer;
}

.hot-rank {
  display: inline-block;
  width: 18px;
  text-align: center;
  font-weight: bold;
}

.hot-count {
  color: #909399;
  font-size: 12px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  color: #606266;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.result-item {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
  cursor: pointer;
  transition: all 0.2s;
}

.result-item:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.result-title {
  font-size: 18px;
  font-weight: 600;
  color: #409EFF;
  margin-bottom: 10px;
}

.result-title :deep(mark) {
  background: #fff3cd;
  padding: 0 2px;
}

.result-summary {
  color: #606266;
  line-height: 1.6;
  margin-bottom: 10px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-summary :deep(mark) {
  background: #fff3cd;
  padding: 0 2px;
}

.result-meta {
  display: flex;
  align-items: center;
  gap: 15px;
  font-size: 13px;
  color: #909399;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-item.relevance {
  color: #67c23a;
  font-weight: 500;
}

.loading-state,
.empty-state {
  padding: 40px 0;
}

:deep(.el-pagination) {
  justify-content: center;
  margin-top: 20px;
}
</style>
