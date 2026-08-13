import { describe, it, expect, vi, beforeEach } from 'vitest'
import { tenantsApi } from '../services/tenants'
import { canAccessTenantsNav, resetAccessCache } from '../utils/access'

vi.mock('../services/tenants')

describe('canAccessTenantsNav', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    resetAccessCache()
  })

  it('returns true when tenants list succeeds', async () => {
    vi.mocked(tenantsApi.list).mockResolvedValue([])
    await expect(canAccessTenantsNav()).resolves.toBe(true)
    expect(tenantsApi.list).toHaveBeenCalledTimes(1)
  })

  it('returns false on HTTP 403', async () => {
    vi.mocked(tenantsApi.list).mockRejectedValue({ response: { status: 403 } })
    await expect(canAccessTenantsNav()).resolves.toBe(false)
  })

  it('keeps nav visible on non-403 errors', async () => {
    vi.mocked(tenantsApi.list).mockRejectedValue({ response: { status: 500 } })
    await expect(canAccessTenantsNav()).resolves.toBe(true)
  })

  it('caches the probe result', async () => {
    vi.mocked(tenantsApi.list).mockResolvedValue([])
    await canAccessTenantsNav()
    await canAccessTenantsNav()
    expect(tenantsApi.list).toHaveBeenCalledTimes(1)
  })
})
