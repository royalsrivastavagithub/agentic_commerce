const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

function getToken(): string | null {
  if (typeof window === "undefined") return null
  try {
    const stored = localStorage.getItem("auth-storage")
    if (!stored) return null
    return JSON.parse(stored)?.state?.token ?? null
  } catch {
    return null
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  opts?: { headers?: Record<string, string> },
): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    ...(opts?.headers ?? {}),
  }
  if (token) headers["Authorization"] = `Bearer ${token}`
  if (body !== undefined && !(body instanceof FormData)) {
    headers["Content-Type"] = "application/json"
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    if (res.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("auth-storage")
      window.location.href = "/auth/login"
    }
    throw new ApiError(res.status, error.detail ?? "Request failed")
  }

  if (res.status === 204) return undefined as T
  return res.json()
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = "ApiError"
  }
}

export const api = {
  get<T>(path: string): Promise<T> {
    return request<T>("GET", path)
  },
  post<T>(path: string, body?: unknown): Promise<T> {
    return request<T>("POST", path, body)
  },
  put<T>(path: string, body?: unknown): Promise<T> {
    return request<T>("PUT", path, body)
  },
  delete<T>(path: string): Promise<T> {
    return request<T>("DELETE", path)
  },
}
