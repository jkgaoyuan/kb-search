<template>
  <div class="document-detail" v-loading="loading">
    <el-page-header @back="$router.back()" title="返回" />

    <div v-if="document" class="document-content">
      <h1 class="doc-title">{{ document.title }}</h1>

      <div class="doc-meta">
        <el-tag :type="fileTypeColor">{{ document.file_type }}</el-tag>
        <span class="meta-item">
          <el-icon><View /></el-icon>
          {{ document.view_count }} 次浏览
        </span>
        <span class="meta-item">
          <el-icon><Timer /></el-icon>
          {{ formatDate(document.updated_at) }}
        </span>
        <el-tag
          v-for="tag in document.tags"
          :key="tag"
          size="small"
          effect="plain"
        >
          {{ tag }}
        </el-tag>
      </div>

      <!-- 解析状态 -->
      <el-alert
        v-if="document.parse_status === 'processing'"
        title="文档正在解析中..."
        type="info"
        :closable="false"
        show-icon
      />

      <el-alert
        v-if="document.parse_status === 'failed'"
        :title="`解析失败: ${document.parse_error || '未知错误'}`"
        type="error"
        :closable="false"
        show-icon
      />

      <!-- 文档内容 -->
      <div v-if="document.content_html" class="doc-body" v-html="document.content_html"></div>
      <div v-else-if="document.content" class="doc-body plain-text">{{ document.content }}</div>
      <div v-else class="doc-body empty">暂无内容</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getDocument } from '@/api/document'

const route = useRoute()
const document = ref(null)
const loading = ref(false)

const fileTypeColor = ref('')
const fileTypeColors = {
  markdown: 'success',
  html: 'warning',
  docx: 'primary'
}

const loadDocument = async () => {
  loading.value = true
  try {
    const res = await getDocument(route.params.id)
    document.value = res
    fileTypeColor.value = fileTypeColors[res.file_type] || 'info'
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

onMounted(loadDocument)
</script>

<style scoped>
.document-detail {
  max-width: 900px;
  margin: 0 auto;
}

.document-content {
  background: #fff;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
  margin-top: 20px;
}

.doc-title {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 15px;
  line-height: 1.4;
}

.doc-meta {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e4e7ed;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #909399;
  font-size: 14px;
}

.doc-body {
  line-height: 1.8;
  color: #303133;
  font-size: 15px;
}

.doc-body :deep(h1),
.doc-body :deep(h2),
.doc-body :deep(h3) {
  margin: 20px 0 10px;
  color: #303133;
}

.doc-body :deep(p) {
  margin: 10px 0;
}

.doc-body :deep(code) {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}

.doc-body :deep(pre) {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 6px;
  overflow-x: auto;
}

.doc-body :deep(blockquote) {
  border-left: 4px solid #409EFF;
  padding-left: 15px;
  margin: 15px 0;
  color: #606266;
}

.doc-body :deep(ul),
.doc-body :deep(ol) {
  padding-left: 25px;
  margin: 10px 0;
}

.doc-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 15px 0;
}

.doc-body :deep(th),
.doc-body :deep(td) {
  border: 1px solid #e4e7ed;
  padding: 10px;
  text-align: left;
}

.doc-body :deep(th) {
  background: #f5f7fa;
  font-weight: 600;
}

.doc-body.plain-text {
  white-space: pre-wrap;
  font-family: -apple-system, BlinkMacSystemFont, sans-serif;
}

.doc-body.empty {
  text-align: center;
  color: #909399;
  padding: 40px 0;
}
</style>
