<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'

import { api } from '../api/client'
import type { Capability } from '../api/types'

const capabilities = ref<Capability[]>([])
const currentName = ref('')
const input = ref('{}')
const result = ref('')
const running = ref(false)
const current = computed(() => capabilities.value.find((item) => item.name === currentName.value))

async function load() {
  capabilities.value = await api<Capability[]>('/agent/capabilities')
  currentName.value ||= capabilities.value[0]?.name ?? ''
}

function useExample() {
  const schema = current.value?.input_schema as { properties?: Record<string, { default?: unknown; type?: string }> }
  const value: Record<string, unknown> = {}
  for (const [key, property] of Object.entries(schema?.properties ?? {})) {
    value[key] = property.default ?? (property.type === 'array' ? [] : property.type === 'object' ? {} : '')
  }
  input.value = JSON.stringify(value, null, 2)
}

async function invoke(mode: 'preview' | 'execute') {
  running.value = true
  try {
    const payload = JSON.parse(input.value)
    const response = await api(`/agent/capabilities/${currentName.value}:invoke`, {
      method: 'POST',
      body: JSON.stringify({ input: payload, mode, confirmed: mode === 'execute', actor_id: 'web-console' }),
    })
    result.value = JSON.stringify(response, null, 2)
    ElMessage.success(mode === 'preview' ? '输入校验通过' : '能力执行完成')
  } catch (error) {
    result.value = error instanceof Error ? error.message : String(error)
    ElMessage.error('能力调用失败')
  } finally { running.value = false }
}

onMounted(load)
</script>

<template>
  <div class="page-head">
    <div><h2>Agent 能力目录</h2><p>API 与 Agent 共用应用服务；写入和高风险能力必须先预览并显式确认。</p></div>
  </div>
  <div class="split">
    <el-card class="panel">
      <el-menu :default-active="currentName" @select="(name: string) => currentName = name">
        <el-menu-item v-for="item in capabilities" :key="item.name" :index="item.name">
          <span style="flex:1">{{ item.name }}</span><el-tag size="small" :type="item.risk === 'read' ? 'success' : item.risk === 'write' ? 'warning' : 'danger'">{{ item.risk }}</el-tag>
        </el-menu-item>
      </el-menu>
    </el-card>
    <el-card v-if="current" class="panel">
      <template #header><div style="display:flex;justify-content:space-between"><strong>{{ current.name }}</strong><span><el-tag>{{ current.module }}</el-tag> <el-tag effect="plain">{{ current.idempotent ? '幂等' : '非幂等' }}</el-tag></span></div></template>
      <p class="muted">{{ current.description }}</p>
      <el-tabs>
        <el-tab-pane label="调用测试">
          <div class="toolbar"><el-button @click="useExample">生成输入骨架</el-button><el-button type="primary" :loading="running" @click="invoke('preview')">预览校验</el-button><el-button type="danger" plain :loading="running" @click="invoke('execute')">确认执行</el-button></div>
          <el-input v-model="input" class="json-editor" type="textarea" :rows="13" />
          <h4>结果</h4><el-input v-model="result" class="json-editor" type="textarea" :rows="10" readonly />
        </el-tab-pane>
        <el-tab-pane label="输入 Schema"><pre>{{ JSON.stringify(current.input_schema, null, 2) }}</pre></el-tab-pane>
        <el-tab-pane label="输出 Schema"><pre>{{ JSON.stringify(current.output_schema, null, 2) }}</pre></el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>
