import { api } from './client'

describe('api client', () => {
  afterEach(() => vi.restoreAllMocks())

  it('returns JSON and preserves request options', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ id: 'p1' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    await expect(api<{ id: string }>('/projects')).resolves.toEqual({ id: 'p1' })
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/projects'),
      expect.objectContaining({ headers: expect.objectContaining({ 'Content-Type': 'application/json' }) }),
    )
  })

  it('converts API errors into a typed error', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({ code: 'RESOURCE_CONFLICT', message: 'duplicate', request_id: 'r1' }),
        { status: 409, headers: { 'Content-Type': 'application/json' } },
      ),
    )
    await expect(api('/projects')).rejects.toMatchObject({
      message: 'duplicate', status: 409, code: 'RESOURCE_CONFLICT', requestId: 'r1',
    })
  })
})
