import { createPinia, setActivePinia } from 'pinia'

import { useProjectStore } from './projects'

describe('project store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })
  afterEach(() => vi.restoreAllMocks())

  it('loads projects and selects the first available project', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify([
          {
            id: 'project-1', name: '采购', slug: 'procurement', description: '',
            status: 'active', timezone: 'Asia/Shanghai', created_at: '', updated_at: '',
          },
        ]),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )
    const store = useProjectStore()
    await store.load()
    expect(store.currentProjectId).toBe('project-1')
    expect(store.currentProject?.name).toBe('采购')
    expect(localStorage.getItem('aidp.currentProjectId')).toBe('project-1')
  })
})
