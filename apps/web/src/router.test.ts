import { routes } from './router'

describe('module routes', () => {
  it('exposes the first vertical modules and the agent capability console', () => {
    expect(routes.map((route) => route.path)).toEqual([
      '/', '/projects', '/data', '/models', '/capabilities',
    ])
  })
})
