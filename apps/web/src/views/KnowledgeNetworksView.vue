<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, reactive, ref, watch } from 'vue'

import { APIError, api } from '../api/client'
import type { ActionType, DataResource, KnowledgeNetwork, ObjectType, RelationType } from '../api/types'
import { useProjectStore } from '../stores/projects'

const store = useProjectStore()
const networks = ref<KnowledgeNetwork[]>([])
const resources = ref<DataResource[]>([])
const objects = ref<ObjectType[]>([])
const relations = ref<RelationType[]>([])
const actions = ref<ActionType[]>([])
const currentNetworkId = ref('')
const networkDialog = ref(false)
const objectDialog = ref(false)
const relationDialog = ref(false)
const actionDialog = ref(false)
const validation = ref<{ valid: boolean; issues: Array<{ level: string; message: string }>; summary: Record<string, number> } | null>(null)
const currentNetwork = computed(() => networks.value.find((item) => item.id === currentNetworkId.value))

const networkForm = reactive({ key: '', name: '', description: '', branch: 'main' })
const objectForm = reactive({
  key: '', name: '', description: '', source_resource_id: '', primary_keys: 'id',
  display_key: 'name', incremental_key: '',
  properties: '[\n  {"key":"id","name":"ID","data_type":"string","nullable":false,"source_field":"id"},\n  {"key":"name","name":"名称","data_type":"string","nullable":false,"source_field":"name"}\n]',
  indexes: '[]',
})
const relationForm = reactive({
  key: '', name: '', source_object_type_id: '', target_object_type_id: '',
  cardinality: 'one_to_many', mapping_type: 'direct',
  mapping: '{"field_pairs":[{"source":"id","target":"parent_id"}]}',
})
const actionForm = reactive({
  key: '', name: '', operation: 'modify', object_type_id: '', permission: 'ask',
  impact_contract: '{"operation":"modify","fields":[]}',
  parameters_schema: '{"type":"object","properties":{},"required":[]}',
  executor: '{"type":"mcp","id":"tool-id"}',
})

function parseJSON(value: string, label: string) {
  try { return JSON.parse(value) }
  catch { throw new Error(`${label} 不是有效 JSON`) }
}

async function loadNetworks() {
  if (!store.currentProjectId) return
  ;[networks.value, resources.value] = await Promise.all([
    api<KnowledgeNetwork[]>(`/projects/${store.currentProjectId}/knowledge-networks`),
    api<DataResource[]>(`/projects/${store.currentProjectId}/data-resources`),
  ])
  if (!networks.value.some((item) => item.id === currentNetworkId.value)) {
    currentNetworkId.value = networks.value[0]?.id ?? ''
  }
  await loadModelParts()
}

async function loadModelParts() {
  validation.value = null
  if (!currentNetworkId.value) { objects.value = []; relations.value = []; actions.value = []; return }
  ;[objects.value, relations.value, actions.value] = await Promise.all([
    api<ObjectType[]>(`/knowledge-networks/${currentNetworkId.value}/object-types`),
    api<RelationType[]>(`/knowledge-networks/${currentNetworkId.value}/relation-types`),
    api<ActionType[]>(`/knowledge-networks/${currentNetworkId.value}/action-types`),
  ])
}

async function createNetwork() {
  await api(`/projects/${store.currentProjectId}/knowledge-networks`, {
    method: 'POST', body: JSON.stringify({ ...networkForm, concept_groups: [] }),
  })
  networkDialog.value = false
  await loadNetworks()
  ElMessage.success('知识网络草稿已创建')
}

async function createObject() {
  try {
    await api(`/knowledge-networks/${currentNetworkId.value}/object-types`, {
      method: 'POST',
      body: JSON.stringify({
        key: objectForm.key, name: objectForm.name, description: objectForm.description,
        source_resource_id: objectForm.source_resource_id || null,
        properties: parseJSON(objectForm.properties, '属性'),
        primary_keys: objectForm.primary_keys.split(',').map((item) => item.trim()).filter(Boolean),
        display_key: objectForm.display_key || null, incremental_key: objectForm.incremental_key || null,
        indexes: parseJSON(objectForm.indexes, '索引'), concept_group: null,
      }),
    })
    objectDialog.value = false
    await loadModelParts()
    ElMessage.success('对象类已创建')
  } catch (error) { ElMessage.error(error instanceof Error ? error.message : '创建失败') }
}

async function createRelation() {
  try {
    await api(`/knowledge-networks/${currentNetworkId.value}/relation-types`, {
      method: 'POST',
      body: JSON.stringify({ ...relationForm, description: '', mapping: parseJSON(relationForm.mapping, '映射'), properties: [] }),
    })
    relationDialog.value = false
    await loadModelParts()
    ElMessage.success('关系类已创建')
  } catch (error) { ElMessage.error(error instanceof Error ? error.message : '创建失败') }
}

async function createAction() {
  try {
    await api(`/knowledge-networks/${currentNetworkId.value}/action-types`, {
      method: 'POST',
      body: JSON.stringify({
        key: actionForm.key, name: actionForm.name, description: '', operation: actionForm.operation,
        object_type_id: actionForm.object_type_id, permission: actionForm.permission, condition: {},
        impact_contract: parseJSON(actionForm.impact_contract, '影响契约'),
        parameters_schema: parseJSON(actionForm.parameters_schema, '参数 Schema'),
        executor: parseJSON(actionForm.executor, '执行器'), retry_policy: {}, compensation: {},
      }),
    })
    actionDialog.value = false
    await loadModelParts()
    ElMessage.success('行动类已创建')
  } catch (error) { ElMessage.error(error instanceof Error ? error.message : '创建失败') }
}

async function validateNetwork() {
  const response = await api<{ valid: boolean; issues: Array<{ level: string; message: string }>; summary: Record<string, number> }>(`/knowledge-networks/${currentNetworkId.value}/validate`, { method: 'POST' })
  validation.value = response
  response.valid ? ElMessage.success('全网校验通过') : ElMessage.warning('存在需要修复的模型问题')
}

async function publishNetwork() {
  await ElMessageBox.confirm('发布后此版本不可直接修改，是否继续？', '发布知识网络', { type: 'warning' })
  try {
    await api(`/knowledge-networks/${currentNetworkId.value}/publish`, { method: 'POST' })
    await loadNetworks()
    ElMessage.success('知识网络已发布')
  } catch (error) {
    ElMessage.error(error instanceof APIError ? error.message : '发布失败')
  }
}

onMounted(loadNetworks)
watch(() => store.currentProjectId, loadNetworks)
watch(currentNetworkId, loadModelParts)
</script>

<template>
  <div v-if="!store.currentProjectId" class="empty-project">请先创建并选择项目。</div>
  <template v-else>
    <div class="page-head">
      <div><h2>知识网络与业务对象模型</h2><p>对象、关系和行动在同一版本内校验并发布，发布版本不可变。</p></div>
      <el-button type="primary" @click="networkDialog = true">新建知识网络</el-button>
    </div>
    <div class="toolbar">
      <el-select v-model="currentNetworkId" placeholder="选择知识网络" style="width: 320px">
        <el-option v-for="item in networks" :key="item.id" :label="`${item.name} v${item.version} · ${item.status}`" :value="item.id" />
      </el-select>
      <template v-if="currentNetwork">
        <el-tag :type="currentNetwork.status === 'published' ? 'success' : 'warning'">{{ currentNetwork.status }}</el-tag>
        <el-button @click="validateNetwork">全网校验</el-button>
        <el-button v-if="currentNetwork.status === 'draft'" type="success" @click="publishNetwork">发布版本</el-button>
      </template>
    </div>
    <el-alert v-if="validation" :type="validation.valid ? 'success' : 'error'" :closable="false" style="margin-bottom: 16px">
      <template #title>对象 {{ validation.summary.objects }} · 关系 {{ validation.summary.relations }} · 行动 {{ validation.summary.actions }} · 错误 {{ validation.summary.errors }} · 警告 {{ validation.summary.warnings }}</template>
      <div v-for="issue in validation.issues" :key="issue.message">{{ issue.level }}：{{ issue.message }}</div>
    </el-alert>
    <el-tabs v-if="currentNetworkId" type="border-card">
      <el-tab-pane label="对象类">
        <div class="toolbar"><el-button :disabled="currentNetwork?.status !== 'draft'" type="primary" @click="objectDialog = true">新建对象类</el-button></div>
        <el-table :data="objects"><el-table-column prop="name" label="名称" /><el-table-column prop="key" label="标识" /><el-table-column label="属性" width="90"><template #default="scope">{{ scope.row.properties.length }}</template></el-table-column><el-table-column label="主键"><template #default="scope">{{ scope.row.primary_keys.join(', ') }}</template></el-table-column><el-table-column prop="display_key" label="显示键" /><el-table-column label="数据源"><template #default="scope">{{ resources.find(item => item.id === scope.row.source_resource_id)?.name ?? '文档/手工' }}</template></el-table-column></el-table>
      </el-tab-pane>
      <el-tab-pane label="关系类">
        <div class="toolbar"><el-button :disabled="currentNetwork?.status !== 'draft' || objects.length < 1" type="primary" @click="relationDialog = true">新建关系类</el-button></div>
        <el-table :data="relations"><el-table-column prop="name" label="名称" /><el-table-column label="源对象"><template #default="scope">{{ objects.find(item => item.id === scope.row.source_object_type_id)?.name }}</template></el-table-column><el-table-column label="目标对象"><template #default="scope">{{ objects.find(item => item.id === scope.row.target_object_type_id)?.name }}</template></el-table-column><el-table-column prop="cardinality" label="基数" /><el-table-column prop="mapping_type" label="映射方式" /></el-table>
      </el-tab-pane>
      <el-tab-pane label="行动类">
        <div class="toolbar"><el-button :disabled="currentNetwork?.status !== 'draft' || objects.length < 1" type="primary" @click="actionDialog = true">新建行动类</el-button></div>
        <el-table :data="actions"><el-table-column prop="name" label="名称" /><el-table-column prop="operation" label="操作" /><el-table-column label="对象"><template #default="scope">{{ objects.find(item => item.id === scope.row.object_type_id)?.name }}</template></el-table-column><el-table-column prop="permission" label="确认策略" /><el-table-column label="执行器"><template #default="scope">{{ scope.row.executor.type }} / {{ scope.row.executor.id }}</template></el-table-column></el-table>
      </el-tab-pane>
    </el-tabs>
  </template>

  <el-dialog v-model="networkDialog" title="新建知识网络" width="520px"><el-form label-position="top"><el-form-item label="名称"><el-input v-model="networkForm.name" /></el-form-item><el-form-item label="标识"><el-input v-model="networkForm.key" placeholder="procurement" /></el-form-item><el-form-item label="说明"><el-input v-model="networkForm.description" type="textarea" /></el-form-item><el-form-item label="分支"><el-input v-model="networkForm.branch" /></el-form-item></el-form><template #footer><el-button @click="networkDialog = false">取消</el-button><el-button type="primary" @click="createNetwork">创建</el-button></template></el-dialog>

  <el-dialog v-model="objectDialog" title="新建对象类" width="720px"><el-form label-position="top"><div class="card-grid" style="grid-template-columns: 1fr 1fr"><el-form-item label="名称"><el-input v-model="objectForm.name" /></el-form-item><el-form-item label="标识"><el-input v-model="objectForm.key" /></el-form-item></div><el-form-item label="数据资源"><el-select v-model="objectForm.source_resource_id" clearable style="width:100%"><el-option v-for="item in resources" :key="item.id" :label="`${item.namespace}.${item.name}`" :value="item.id" /></el-select></el-form-item><el-form-item label="属性 JSON"><el-input v-model="objectForm.properties" class="json-editor" type="textarea" :rows="10" /></el-form-item><div class="card-grid"><el-form-item label="主键"><el-input v-model="objectForm.primary_keys" /></el-form-item><el-form-item label="显示键"><el-input v-model="objectForm.display_key" /></el-form-item><el-form-item label="增量键"><el-input v-model="objectForm.incremental_key" /></el-form-item></div><el-form-item label="索引 JSON"><el-input v-model="objectForm.indexes" class="json-editor" type="textarea" :rows="3" /></el-form-item></el-form><template #footer><el-button @click="objectDialog = false">取消</el-button><el-button type="primary" @click="createObject">创建</el-button></template></el-dialog>

  <el-dialog v-model="relationDialog" title="新建关系类" width="650px"><el-form label-position="top"><div class="card-grid" style="grid-template-columns:1fr 1fr"><el-form-item label="名称"><el-input v-model="relationForm.name" /></el-form-item><el-form-item label="标识"><el-input v-model="relationForm.key" /></el-form-item></div><div class="card-grid" style="grid-template-columns:1fr 1fr"><el-form-item label="源对象"><el-select v-model="relationForm.source_object_type_id"><el-option v-for="item in objects" :key="item.id" :label="item.name" :value="item.id" /></el-select></el-form-item><el-form-item label="目标对象"><el-select v-model="relationForm.target_object_type_id"><el-option v-for="item in objects" :key="item.id" :label="item.name" :value="item.id" /></el-select></el-form-item></div><div class="card-grid" style="grid-template-columns:1fr 1fr"><el-form-item label="基数"><el-select v-model="relationForm.cardinality"><el-option v-for="item in ['one_to_one','one_to_many','many_to_many']" :key="item" :label="item" :value="item" /></el-select></el-form-item><el-form-item label="映射方式"><el-select v-model="relationForm.mapping_type"><el-option v-for="item in ['direct','data_view','filtered_cross_join']" :key="item" :label="item" :value="item" /></el-select></el-form-item></div><el-form-item label="映射 JSON"><el-input v-model="relationForm.mapping" class="json-editor" type="textarea" :rows="5" /></el-form-item></el-form><template #footer><el-button @click="relationDialog = false">取消</el-button><el-button type="primary" @click="createRelation">创建</el-button></template></el-dialog>

  <el-dialog v-model="actionDialog" title="新建行动类" width="700px"><el-form label-position="top"><div class="card-grid"><el-form-item label="名称"><el-input v-model="actionForm.name" /></el-form-item><el-form-item label="标识"><el-input v-model="actionForm.key" /></el-form-item><el-form-item label="操作"><el-select v-model="actionForm.operation"><el-option v-for="item in ['add','modify','delete']" :key="item" :label="item" :value="item" /></el-select></el-form-item></div><div class="card-grid" style="grid-template-columns:2fr 1fr"><el-form-item label="对象"><el-select v-model="actionForm.object_type_id"><el-option v-for="item in objects" :key="item.id" :label="item.name" :value="item.id" /></el-select></el-form-item><el-form-item label="确认策略"><el-select v-model="actionForm.permission"><el-option v-for="item in ['allow','ask','deny']" :key="item" :label="item" :value="item" /></el-select></el-form-item></div><el-form-item label="影响契约"><el-input v-model="actionForm.impact_contract" class="json-editor" type="textarea" :rows="3" /></el-form-item><el-form-item label="参数 Schema"><el-input v-model="actionForm.parameters_schema" class="json-editor" type="textarea" :rows="4" /></el-form-item><el-form-item label="执行器"><el-input v-model="actionForm.executor" class="json-editor" type="textarea" :rows="3" /></el-form-item></el-form><template #footer><el-button @click="actionDialog = false">取消</el-button><el-button type="primary" @click="createAction">创建</el-button></template></el-dialog>
</template>
