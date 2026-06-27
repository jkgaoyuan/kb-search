<template>
  <div class="upload-view">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>上传文档</span>
          <el-tag type="info">支持 Markdown / HTML / DOCX</el-tag>
        </div>
      </template>

      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="文档标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入文档标题" />
        </el-form-item>

        <el-form-item label="所属分类" prop="category_id">
          <el-cascader
            v-model="form.category_id"
            :options="categoryOptions"
            :props="{ value: 'id', label: 'name', checkStrictly: true }"
            placeholder="选择分类"
            clearable
          />
        </el-form-item>

        <el-form-item label="标签">
          <el-select
            v-model="form.tags"
            multiple
            filterable
            allow-create
            placeholder="输入标签，按回车确认"
            style="width: 100%"
          >
            <el-option
              v-for="tag in commonTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="上传文件" prop="file">
          <el-upload
            ref="uploadRef"
            action="#"
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :limit="1"
            accept=".md,.markdown,.html,.htm,.docx"
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon>
              选择文件
            </el-button>
            <template #tip>
              <div class="upload-tip">
                支持 Markdown (.md), HTML (.html), Word (.docx) 格式，单个文件不超过 20MB
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="uploading"
            @click="handleSubmit"
          >
            上传文档
          </el-button>
          <el-button size="large" @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 上传进度 -->
      <div v-if="uploadResult" class="upload-result">
        <el-alert
          :title="uploadResult.message"
          :type="uploadResult.parse_status === 'pending' ? 'info' : 'success'"
          show-icon
          :closable="false"
        >
          <template #default>
            <p>文档ID: {{ uploadResult.id }}</p>
            <p>解析状态: {{ parseStatusText }}</p>
            <el-progress
              v-if="parseProgress < 100"
              :percentage="parseProgress"
              :status="parseProgress === 100 ? 'success' : ''"
            />
          </template>
        </el-alert>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { uploadDocument, getDocumentStatus } from '@/api/document'
import { getCategories } from '@/api/category'

const formRef = ref()
const uploadRef = ref()
const uploading = ref(false)
const uploadResult = ref(null)
const parseProgress = ref(0)
const categoryOptions = ref([])
const commonTags = ref(['技术', '产品', '运营', '教程', '最佳实践'])
let statusTimer = null

const form = reactive({
  title: '',
  category_id: null,
  tags: [],
  file: null
})

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }],
  file: [{ required: true, message: '请上传文件', trigger: 'change' }]
}

const parseStatusText = computed(() => {
  const statusMap = {
    pending: '等待解析',
    processing: '解析中...',
    completed: '解析完成',
    failed: '解析失败'
  }
  return statusMap[uploadResult.value?.parse_status] || '未知'
})

// 加载分类
const loadCategories = async () => {
  try {
    const res = await getCategories({ tree: true })
    categoryOptions.value = buildTree(res.items || [])
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

loadCategories()

const handleFileChange = (file) => {
  form.file = file.raw
}

const handleFileRemove = () => {
  form.file = null
}

const handleSubmit = async () => {
  await formRef.value.validate()

  if (!form.file) {
    ElMessage.warning('请选择文件')
    return
  }

  uploading.value = true

  try {
    const categoryId = Array.isArray(form.category_id) 
      ? form.category_id[form.category_id.length - 1] 
      : form.category_id

    const res = await uploadDocument({
      title: form.title,
      category_id: categoryId,
      tags: form.tags.join(','),
      file: form.file
    })

    uploadResult.value = res
    parseProgress.value = 0
    ElMessage.success('上传成功，正在解析')

    // 轮询解析状态
    startStatusPolling(res.id)

  } catch (e) {
    console.error(e)
  } finally {
    uploading.value = false
  }
}

const startStatusPolling = (docId) => {
  if (statusTimer) clearInterval(statusTimer)

  statusTimer = setInterval(async () => {
    try {
      const status = await getDocumentStatus(docId)

      if (status.parse_status === 'completed') {
        parseProgress.value = 100
        uploadResult.value.parse_status = 'completed'
        clearInterval(statusTimer)
        ElMessage.success('文档解析完成')
      } else if (status.parse_status === 'failed') {
        parseProgress.value = 0
        uploadResult.value.parse_status = 'failed'
        uploadResult.value.parse_error = status.parse_error
        clearInterval(statusTimer)
        ElMessage.error('文档解析失败')
      } else {
        parseProgress.value = Math.min(parseProgress.value + 20, 90)
      }
    } catch (e) {
      clearInterval(statusTimer)
    }
  }, 2000)
}

const resetForm = () => {
  formRef.value.resetFields()
  uploadRef.value.clearFiles()
  form.file = null
  uploadResult.value = null
  parseProgress.value = 0
  if (statusTimer) clearInterval(statusTimer)
}

onUnmounted(() => {
  if (statusTimer) clearInterval(statusTimer)
})
</script>

<style scoped>
.upload-view {
  max-width: 700px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-tip {
  color: #909399;
  font-size: 13px;
  margin-top: 8px;
}

.upload-result {
  margin-top: 20px;
}
</style>
