const baseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

export class APIError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code?: string,
    public readonly requestId?: string,
  ) {
    super(message)
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new APIError(
      body.message ?? `请求失败（${response.status}）`,
      response.status,
      body.code,
      body.request_id,
    )
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}
