<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref, watch } from 'vue'

import { api } from '../api/client'
import type { Catalog, ConnectorType, DataResource, Secret } from '../api/types'
import { useProjectStore } from '../stores/projects'

const store = useProjectStore()
const catalogs = ref<Catalog[]>([])
const connectors = ref<ConnectorType[]>([])
const resources = ref<DataResource[]>([])
const secrets = ref<Secret[]>([])
const loading = ref(false)
const catalogDialog = ref(false)
const secretDialog = ref(false)
const testing = ref('')
const discovering = ref('')
const secretForm = reactive({ name: '', username: '', password: '' })
const catalogForm = reactive({
  name: '', description: '', connector_type: 'postgresql', secret_id: '', host: 'localhost',
  port: 5432, database: '', schemas: 'public', sslmode: 'prefer', read_only: true,
})

async function load() {
  if (!store.currentProjectId) return
  loading.value = true
  try {
    ;[catalogs.value, resources.value, secrets.value] = await Promise.all([
      api<Catalog[]>(`/projects/${store.currentProjectId}/catalogs`),
      api<DataResource[]>(`/projects/${store.currentProjectId}/data-resources`),
      api<Secret[]>(`/projects/${store.currentProjectId}/secrets`),
    ])
  } finally { loading.value = false }
}

async function createSecret() {
  await api(`/projects/${store.currentProjectId}/secrets`, {
    method: 'POST',
    body: JSON.stringify({
      name: secretForm.name, kind: 'database_credentials',
      value: JSON.stringify({ username: secretForm.username, password: secretForm.password }),
    }),
  })
  secretDialog.value = false
  Object.assign(secretForm, { name: '', username: '', password: '' })
  await load()
  ElMessage.success('凭证已加密保存')
}

async function createCatalog() {
  await api(`/projects/${store.currentProjectId}/catalogs`, {
    method: 'POST',
    body: JSON.stringify({
      name: catalogForm.name, description: catalogForm.description,
      connector_type: catalogForm.connector_type, secret_id: catalogForm.secret_id || null,
      config: {
        host: catalogForm.host, port: Number(catalogForm.port), database: catalogForm.database,
        schemas: catalogForm.schemas.split(',').map((item) => item.trim()).filter(Boolean),
        sslmode: catalogForm.sslmode,
      },
      scope: 'project', read_only: catalogForm.read_only,
    }),
  })
  catalogDialog.value = false
  await load()
  ElMessage.success('数据连接已创建')
}

async function testCatalog(item: Catalog) {
  testing.value = item.id
  try {
    const result = await api<{ ok: boolean; error?: string }>(`/catalogs/${item.id}/test`, { method: 'POST' })
    result.ok ? ElMessage.success('连接测试通过') : ElMessage.error(result.error ?? '连接失败')
    await load()
  } finally { testing.value = '' }
}

async function discover(item: Catalog) {
  discovering.value = item.id
  try {
    const result = await api<{ status: string; message: string; statistics: Record<string, number> }>(`/catalogs/${item.id}/discover-tasks`, {
      method: 'POST', body: JSON.stringify({ strategy: 'full_sync', schemas: item.config.schemas ?? [] }),
    })
    result.status === 'completed' ? ElMessage.success(result.message) : ElMessage.error(result.message)
    await load()
  } finally { discovering.value = '' }
}

onMounted(async () => { connectors.value = await api<ConnectorType[]>('/connector-types'); await load() })
watch(() => store.currentProjectId, load)
</script>

<template>
  <div v-if="!store.currentProjectId" class="empty-project">请先创建并选择项目。</div>
  <template v-else>
    <div class="page-head">
      <div><h2>Catalog 与资源发现</h2><p>凭证与连接配置分离；缺失资源先标记 stale，避免破坏下游模型。</p></div>
      <div><el-button @click="secretDialog = true">新建 Secret</el-button><el-button type="primary" @click="catalogDialog = true">新建连接</el-button></div>
    </div>
    <el-card class="panel">
      <template #header><strong>数据连接</strong></template>
      <el-table :data="catalogs" v-loading="loading">
        <el-table-column prop="name" label="名称" min-width="170" />
        <el-table-column prop="connector_type" label="连接器" width="130" />
        <el-table-column label="目标" min-width="220"><template #default="scope">{{ scope.row.config.host }} / {{ scope.row.config.database }}</template></el-table-column>
        <el-table-column label="状态" width="130"><template #default="scope"><span :class="['status-dot', scope.row.status]" />{{ scope.row.status }}</template></el-table-column>
        <el-table-column label="操作" width="210"><template #default="scope"><el-button link type="primary" :loading="testing === scope.row.id" @click="testCatalog(scope.row)">测试</el-button><el-button link type="primary" :loading="discovering === scope.row.id" @click="discover(scope.row)">发现资源</el-button></template></el-table-column>
      </el-table>
    </el-card>
    <el-card class="panel">
      <template #header><strong>数据资源</strong></template>
      <el-table :data="resources">
        <el-table-column prop="namespace" label="Schema" width="150" />
        <el-table-column prop="name" label="资源" min-width="180" />
        <el-table-column prop="category" label="类型" width="100" />
        <el-table-column label="字段" width="90"><template #default="scope">{{ scope.row.schema.fields?.length ?? 0 }}</template></el-table-column>
        <el-table-column label="主键" min-width="180"><template #default="scope">{{ scope.row.schema.primary_key?.join(', ') || '—' }}</template></el-table-column>
        <el-table-column label="发现状态" width="120"><template #default="scope"><el-tag effect="plain">{{ scope.row.discovery_status }}</el-tag></template></el-table-column>
        <el-table-column label="资源状态" width="110"><template #default="scope"><span :class="['status-dot', scope.row.status]" />{{ scope.row.status }}</template></el-table-column>
      </el-table>
    </el-card>
  </template>

  <el-dialog v-model="secretDialog" title="新建数据库凭证" width="500px">
    <el-alert title="凭证加密保存，创建后不会回显。" type="info" :closable="false" />
    <el-form label-position="top" style="margin-top: 16px">
      <el-form-item label="Secret 名称"><el-input v-model="secretForm.name" /></el-form-item>
      <el-form-item label="用户名"><el-input v-model="secretForm.username" /></el-form-item>
      <el-form-item label="密码"><el-input v-model="secretForm.password" type="password" show-password /></el-form-item>
    </el-form>
    <template #footer><el-button @click="secretDialog = false">取消</el-button><el-button type="primary" @click="createSecret">保存</el-button></template>
  </el-dialog>

  <el-dialog v-model="catalogDialog" title="新建数据连接" width="620px">
    <el-form label-position="top">
      <el-form-item label="连接名称"><el-input v-model="catalogForm.name" /></el-form-item>
      <el-form-item label="连接器"><el-select v-model="catalogForm.connector_type" style="width: 100%"><el-option v-for="item in connectors" :key="item.id" :label="item.name" :value="item.id" /></el-select></el-form-item>
      <div class="card-grid" style="grid-template-columns: 2fr 1fr"><el-form-item label="Host"><el-input v-model="catalogForm.host" /></el-form-item><el-form-item label="Port"><el-input-number v-model="catalogForm.port" :min="1" :max="65535" /></el-form-item></div>
      <el-form-item label="Database"><el-input v-model="catalogForm.database" /></el-form-item>
      <el-form-item label="Schemas（逗号分隔）"><el-input v-model="catalogForm.schemas" /></el-form-item>
      <el-form-item label="凭证"><el-select v-model="catalogForm.secret_id" clearable style="width: 100%"><el-option v-for="item in secrets" :key="item.id" :label="item.name" :value="item.id" /></el-select></el-form-item>
      <el-form-item label="SSL Mode"><el-select v-model="catalogForm.sslmode" style="width: 100%"><el-option v-for="item in ['disable','prefer','require','verify-ca','verify-full']" :key="item" :label="item" :value="item" /></el-select></el-form-item>
      <el-checkbox v-model="catalogForm.read_only">只读连接</el-checkbox>
    </el-form>
    <template #footer><el-button @click="catalogDialog = false">取消</el-button><el-button type="primary" @click="createCatalog">创建</el-button></template>
  </el-dialog>
</template>
