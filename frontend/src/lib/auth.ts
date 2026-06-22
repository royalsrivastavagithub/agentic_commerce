import { decodeJwt } from "jose"

export interface JwtPayload {
  sub: string
  role: string
  exp: number
}

export function decodeToken(token: string): JwtPayload | null {
  try {
    return decodeJwt(token) as JwtPayload
  } catch {
    return null
  }
}

export function isTokenExpired(token: string): boolean {
  const payload = decodeToken(token)
  if (!payload?.exp) return true
  return Date.now() >= payload.exp * 1000
}

