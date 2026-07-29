<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'

import { api } from '../api/client'
import type { Project } from '../api/types'
import { useProjectStore } from '../stores/projects'

const store = useProjectStore()
const dialogVisible = ref(false)
const saving = ref(false)
const form = reactive({ name: '', slug: '', description: '', timezone: 'Asia/Shanghai' })

async function createProject() {
  saving.value = true
  try {
    const project = await api<Project>('/projects', { method: 'POST', body: JSON.stringify(form) })
    await store.load()
    store.select(project.id)
    dialogVisible.value = false
    Object.assign(form, { name: '', slug: '', description: '', timezone: 'Asia/Shanghai' })
    ElMessage.success('项目已创建')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="page-head">
    <div><h2>项目空间</h2><p>项目是数据、模型、能力和 Agent 的权限边界。</p></div>
    <el-button type="primary" @click="dialogVisible = true">新建项目</el-button>
  </div>
  <el-card class="panel">
    <el-table :data="store.projects" v-loading="store.loading">
      <el-table-column prop="name" label="名称" min-width="180" />
      <el-table-column prop="slug" label="标识" min-width="160" />
      <el-table-column prop="description" label="说明" min-width="260" show-overflow-tooltip />
      <el-table-column prop="timezone" label="时区" width="150" />
      <el-table-column label="状态" width="110"><template #default="scope"><el-tag>{{ scope.row.status }}</el-tag></template></el-table-column>
      <el-table-column label="操作" width="120"><template #default="scope"><el-button link type="primary" @click="store.select(scope.row.id)">设为当前</el-button></template></el-table-column>
    </el-table>
  </el-card>
  <el-dialog v-model="dialogVisible" title="新建项目" width="520px">
    <el-form label-position="top">
      <el-form-item label="项目名称"><el-input v-model="form.name" /></el-form-item>
      <el-form-item label="项目标识"><el-input v-model="form.slug" placeholder="procurement-demo" /></el-form-item>
      <el-form-item label="说明"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
      <el-form-item label="默认时区"><el-input v-model="form.timezone" /></el-form-item>
    </el-form>
    <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="createProject">创建</el-button></template>
  </el-dialog>
</template>
