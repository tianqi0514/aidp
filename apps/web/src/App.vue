<script setup lang="ts">
import { Connection, Grid, Link, Opportunity, Setting } from '@element-plus/icons-vue'
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'

import { useProjectStore } from './stores/projects'

const route = useRoute()
const projects = useProjectStore()
const title = computed(() => route.meta.title ?? 'AIDP')

onMounted(() => projects.load())
</script>

<template>
  <el-container class="shell">
    <el-aside width="232px" class="sidebar">
      <div class="brand">
        <div class="brand-mark">A</div>
        <div><strong>AIDP</strong><small>智能决策平台</small></div>
      </div>
      <el-menu :default-active="route.path" router class="nav">
        <el-menu-item index="/"><el-icon><Grid /></el-icon><span>工作台</span></el-menu-item>
        <el-menu-item index="/projects"><el-icon><Setting /></el-icon><span>项目</span></el-menu-item>
        <el-menu-item index="/data"><el-icon><Connection /></el-icon><span>数据连接</span></el-menu-item>
        <el-menu-item index="/models"><el-icon><Link /></el-icon><span>业务对象模型</span></el-menu-item>
        <el-menu-item index="/capabilities"><el-icon><Opportunity /></el-icon><span>Agent 能力</span></el-menu-item>
      </el-menu>
      <div class="sidebar-footer">
        <span>当前项目</span>
        <el-select
          :model-value="projects.currentProjectId"
          placeholder="选择项目"
          @change="projects.select"
        >
          <el-option v-for="item in projects.projects" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </div>
    </el-aside>
    <el-container>
      <el-header class="topbar"><h1>{{ title }}</h1><el-tag type="success" effect="plain">开发预览</el-tag></el-header>
      <el-main class="content"><router-view /></el-main>
    </el-container>
  </el-container>
</template>
