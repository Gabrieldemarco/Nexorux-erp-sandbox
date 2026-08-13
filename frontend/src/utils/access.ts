/** Lightweight UI access probes with module cache (avoids spam on Layout remounts). */

import { tenantsApi } from '../services/tenants'

let tenantsAllowed: boolean | null = null
let tenantsProbe: Promise<boolean> | null = null

export function canAccessTenantsNav(): Promise<boolean> {
  if (tenantsAllowed !== null) return Promise.resolve(tenantsAllowed)
  if (!tenantsProbe) {
    tenantsProbe = tenantsApi
      .list()
      .then(() => {
        tenantsAllowed = true
        return true
      })
      .catch((err: { response?: { status?: number } }) => {
        // Only hide on explicit forbidden; keep visible on network/auth transient errors
        tenantsAllowed = err?.response?.status !== 403
        return tenantsAllowed
      })
      .finally(() => {
        tenantsProbe = null
      })
  }
  return tenantsProbe
}

export function resetAccessCache() {
  tenantsAllowed = null
  tenantsProbe = null
}
