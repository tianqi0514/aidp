import { defineStore } from 'pinia'

import { api } from '../api/client'
import type { Project } from '../api/types'

const storageKey = 'aidp.currentProjectId'

export const useProjectStore = defineStore('projects', {
  state: () => ({
    projects: [] as Project[],
    currentProjectId: localStorage.getItem(storageKey) ?? '',
    loading: false,
  }),
  getters: {
    currentProject(state): Project | undefined {
      return state.projects.find((item) => item.id === state.currentProjectId)
    },
  },
  actions: {
    async load() {
      this.loading = true
      try {
        this.projects = await api<Project[]>('/projects')
        if (!this.projects.some((item) => item.id === this.currentProjectId)) {
          this.select(this.projects[0]?.id ?? '')
        }
      } finally {
        this.loading = false
      }
    },
    select(id: string) {
      this.currentProjectId = id
      if (id) localStorage.setItem(storageKey, id)
      else localStorage.removeItem(storageKey)
    },
  },
})
