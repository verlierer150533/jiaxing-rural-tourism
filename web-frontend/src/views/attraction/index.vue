<template>
  <div>
    <div class="toolbar">
      <h3 class="page-title">资源管理</h3>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon> 新增资源
      </el-button>
    </div>

    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="名称 / 镇街 / 简介" clearable style="width: 200px"
            @keyup.enter="reload" />
        </el-form-item>
        <el-form-item label="类别">
          <el-select v-model="filters.category" placeholder="全部" clearable style="width: 130px">
            <el-option v-for="item in categories" :key="item.name" :label="`${item.name}（${item.count}）`"
              :value="item.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="镇街">
          <el-select v-model="filters.town" placeholder="全部" clearable style="width: 150px">
            <el-option v-for="item in towns" :key="item.name" :label="`${item.name}（${item.count}）`"
              :value="item.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="已上架" :value="1" />
            <el-option label="已下架" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="reload">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="rows" stripe style="width: 100%">
        <el-table-column prop="name" label="名称" min-width="160" show-overflow-tooltip />
        <el-table-column label="类别" width="90">
          <template #default="{ row }">
            <el-tag :type="categoryTagType(row.category)" size="small" effect="plain">
              {{ row.category }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="town" label="镇街" width="100" />
        <el-table-column prop="address" label="地址" min-width="200" show-overflow-tooltip />
        <el-table-column label="经纬度" width="170">
          <template #default="{ row }">
            <span class="mono">{{ Number(row.longitude).toFixed(4) }}, {{ Number(row.latitude).toFixed(4) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="view_count" label="浏览量" width="90" align="right" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch :model-value="row.status === 1" @change="onToggleStatus(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total"
          :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next" background
          @size-change="reload" @current-change="load" />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑资源' : '新增资源'" width="640px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="88px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="名称" prop="name">
              <el-input v-model="form.name" placeholder="如：盐官古镇" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="类别" prop="category">
              <el-select v-model="form.category" placeholder="请选择" style="width: 100%">
                <el-option v-for="item in categories" :key="item.name" :label="item.name" :value="item.name" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="镇街" prop="town">
              <el-select v-model="form.town" placeholder="请选择" filterable allow-create style="width: 100%">
                <el-option v-for="item in towns" :key="item.name" :label="item.name" :value="item.name" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="排序">
              <el-input-number v-model="form.sort" :min="0" :max="9999" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="地址">
          <el-input v-model="form.address" placeholder="浙江省嘉兴市海宁市……" />
        </el-form-item>

        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="经度" prop="longitude">
              <el-input-number v-model="form.longitude" :precision="6" :step="0.0001" :controls="false"
                style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="纬度" prop="latitude">
              <el-input-number v-model="form.latitude" :precision="6" :step="0.0001" :controls="false"
                style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="简介">
          <el-input v-model="form.summary" type="textarea" :rows="2" maxlength="120" show-word-limit />
        </el-form-item>

        <el-form-item label="详情">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>

        <el-form-item label="外链">
          <el-input v-model="form.external_url" placeholder="导流链接（可空，不做站内支付）" />
        </el-form-item>

        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">上架</el-radio>
            <el-radio :value="0">下架</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  createAttraction,
  deleteAttraction,
  fetchAdminAttractions,
  fetchMeta,
  toggleAttractionStatus,
  updateAttraction
} from '@/api/attraction'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

const categories = ref([])
const towns = ref([])

const filters = reactive({ keyword: '', category: '', town: '', status: '' })

const dialogVisible = ref(false)
const editingId = ref(null)
const formRef = ref(null)

const emptyForm = () => ({
  name: '',
  category: '',
  town: '',
  address: '',
  longitude: 120.68,
  latitude: 30.47,
  summary: '',
  description: '',
  external_url: '',
  sort: 10,
  status: 1
})

const form = reactive(emptyForm())

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  category: [{ required: true, message: '请选择类别', trigger: 'change' }],
  longitude: [{ required: true, message: '请输入经度', trigger: 'blur' }],
  latitude: [{ required: true, message: '请输入纬度', trigger: 'blur' }]
}

function categoryTagType(category) {
  return { 古镇: 'warning', 果园: 'success', 村落: 'primary', 景区: 'info' }[category] || 'info'
}

async function loadMeta() {
  const meta = await fetchMeta()
  categories.value = meta.categories || []
  towns.value = meta.towns || []
}

async function load() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
      keyword: filters.keyword || undefined,
      category: filters.category || undefined,
      town: filters.town || undefined
    }
    if (filters.status !== '' && filters.status !== null) {
      params.status = filters.status
    }
    const data = await fetchAdminAttractions(params)
    rows.value = data.list || []
    total.value = data.total || 0
  } finally {
    loading.value = false
  }
}

function reload() {
  page.value = 1
  load()
}

function resetFilters() {
  filters.keyword = ''
  filters.category = ''
  filters.town = ''
  filters.status = ''
  reload()
}

function openCreate() {
  editingId.value = null
  Object.assign(form, emptyForm())
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    category: row.category,
    town: row.town,
    address: row.address,
    longitude: Number(row.longitude),
    latitude: Number(row.latitude),
    summary: row.summary,
    description: row.description,
    external_url: row.external_url,
    sort: row.sort,
    status: row.status
  })
  dialogVisible.value = true
}

async function onSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    if (editingId.value) {
      await updateAttraction(editingId.value, { ...form })
      ElMessage.success('已保存')
    } else {
      await createAttraction({ ...form })
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    await Promise.all([load(), loadMeta()])
  } finally {
    saving.value = false
  }
}

async function onToggleStatus(row) {
  const next = row.status === 1 ? 0 : 1
  await toggleAttractionStatus(row.id, next)
  row.status = next
  ElMessage.success(next === 1 ? '已上架' : '已下架')
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确认删除「${row.name}」？该操作不可恢复。`, '删除确认', {
    type: 'warning'
  })
  await deleteAttraction(row.id)
  ElMessage.success('已删除')
  await Promise.all([load(), loadMeta()])
}

onMounted(async () => {
  await loadMeta()
  await load()
})
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.toolbar .page-title {
  margin: 0;
}

.filter-card {
  margin-bottom: 12px;
}

.filter-card :deep(.el-form-item) {
  margin-bottom: 4px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}

.mono {
  font-family: Consolas, Monaco, monospace;
  font-size: 12px;
}
</style>
