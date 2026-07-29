<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { api } from '../api/client'
import type { Capability, Catalog, KnowledgeNetwork } from '../api/types'
import { useProjectStore } from '../stores/projects'

const store = useProjectStore()
const catalogs = ref<Catalog[]>([])
const networks = ref<KnowledgeNetwork[]>([])
const capabilities = ref<Capability[]>([])
const healthyCatalogs = computed(() => catalogs.value.filter((item) => item.status === 'healthy').length)
const publishedNetworks = computed(() => networks.value.filter((item) => item.status === 'published').length)

async function load() {
  capabilities.value = await api<Capability[]>('/agent/capabilities')
  if (!store.currentProjectId) return
  ;[catalogs.value, networks.value] = await Promise.all([
    api<Catalog[]>(`/projects/${store.currentProjectId}/catalogs`),
    api<KnowledgeNetwork[]>(`/projects/${store.currentProjectId}/knowledge-networks`),
  ])
}

onMounted(load)
watch(() => store.currentProjectId, load)
</script>

<template>
  <div class="page-head">
    <div><h2>从数据与业务模型开始</h2><p>每个后台操作都通过同一应用服务暴露给 API 与内置 Agent。</p></div>
  </div>
  <div class="card-grid">
    <el-card class="metric-card"><span class="muted">项目</span><div class="metric-value">{{ store.projects.length }}</div></el-card>
    <el-card class="metric-card"><span class="muted">健康连接</span><div class="metric-value">{{ healthyCatalogs }} / {{ catalogs.length }}</div></el-card>
    <el-card class="metric-card"><span class="muted">Agent 能力</span><div class="metric-value">{{ capabilities.length }}</div></el-card>
  </div>
  <el-card class="panel" style="margin-top: 18px">
    <template #header><strong>当前项目交付链路</strong></template>
    <el-steps :active="publishedNetworks > 0 ? 4 : healthyCatalogs > 0 ? 2 : catalogs.length > 0 ? 1 : 0" finish-status="success">
      <el-step title="创建连接" description="Catalog + Secret" />
      <el-step title="测试连接" description="健康与权限" />
      <el-step title="发现资源" description="元数据与差异" />
      <el-step title="业务建模" description="对象、关系、行动" />
      <el-step title="发布模型" description="全网校验" />
    </el-steps>
  </el-card>
</template>
