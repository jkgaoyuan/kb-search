<template>
  <div class="category-view">
    <h2>知识分类</h2>

    <div class="category-tree">
      <el-tree
        :data="treeData"
        :props="{ label: 'name', children: 'children' }"
        node-key="id"
        default-expand-all
        highlight-current
        @node-click="handleNodeClick"
      >
        <template #default="{ node, data }">
          <div class="tree-node">
            <el-icon v-if="data.children && data.children.length">
              <Folder v-if="!node.expanded" />
              <FolderOpened v-else />
            </el-icon>
            <el-icon v-else><Document /></el-icon>
            <span class="node-name">{{ data.name }}</span>
            <el-tag v-if="data.doc_count" size="small" type="info">{{ data.doc_count }}</el-tag>
          </div>
        </template>
      </el-tree>
    </div>

    <!-- 分类下的文档 -->
    <div v-if="selectedCategory" class="category-docs">
      <div class="docs-header">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item>分类</el-breadcrumb-item>
          <el-breadcrumb-item
            v-for="item in breadcrumbs"
            :key="item.id"
          >
            {{ item.name }}
          </el-breadcrumb-item>
        </el-breadcrumb>
      </div>

      <div v-if="documents.length > 0" class="doc-list">
        <div
          v-for="doc in documents"
          :key="doc.id"
          class="doc-item"
          @click="goToDetail(doc.id)"
        >
          <div class="doc-title">{{ doc.title }}</div>
          <div class="doc-meta">
            <el-tag size="small" type="info">{{ doc.file_type }}</el-tag>
            <span>{{ doc.view_count }} 次浏览</span>
            <span>{{ formatDate(doc.updated_at) }}</span>
          </div>
        </div>
      </div>
      <el-empty v-else description="该分类下暂无文档" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getCategories, getBreadcrumb } from '@/api/category'
import { getDocuments } from '@/api/document'

const router = useRouter()
const treeData = ref([])
const selectedCategory = ref(null)
const breadcrumbs = ref([])
const documents = ref([])

const loadCategories = async () => {
  try {
    const res = await getCategories({ tree: true })
    treeData.value = buildTree(res.items || [])
  } catch (e) {
    console.error(e)
  }
}

const buildTree = (items) => {
  const map = {}
  const roots = []

  items.forEach(item => {
    map[item.id] = { ...item, children: [] }
  })

  items.forEach(item => {
    if (item.parent_id && map[item.parent_id]) {
      map[item.parent_id].children.push(map[item.id])
    } else {
      roots.push(map[item.id])
    }
  })

  return roots
}

const handleNodeClick = async (data) => {
  selectedCategory.value = data

  // 加载面包屑
  try {
    const bc = await getBreadcrumb(data.id)
    breadcrumbs.value = bc.breadcrumbs || []
  } catch (e) {
    breadcrumbs.value = [{ id: data.id, name: data.name }]
  }

  // 加载文档
  try {
    const res = await getDocuments({ category_id: data.id, page_size: 100 })
    documents.value = res.items || []
  } catch (e) {
    documents.value = []
  }
}

const goToDetail = (id) => {
  router.push(`/document/${id}`)
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

onMounted(loadCategories)
</script>

<style scoped>
.category-view {
  display: flex;
  gap: 20px;
}

.category-view h2 {
  margin-bottom: 15px;
  color: #303133;
}

.category-tree {
  width: 280px;
  background: #fff;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
  flex-shrink: 0;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
}

.node-name {
  flex: 1;
}

.category-docs {
  flex: 1;
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
}

.docs-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e4e7ed;
}

.doc-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.doc-item {
  padding: 15px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.doc-item:hover {
  border-color: #409EFF;
  box-shadow: 0 2px 8px rgba(64,158,255,0.1);
}

.doc-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 8px;
}

.doc-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: #909399;
}
</style>
