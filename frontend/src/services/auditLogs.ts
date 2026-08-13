import { api } from './api'

export interface AuditLogResponse {
  id: string
  tenant_id: string
  company_id?: string | null
  user_id?: string | null
  action: string
  entity: string
  entity_id: string
  changes?: Record<string, unknown> | null
  ip_address?: string | null
  request_id?: string | null
  timestamp?: string | null
  created_at: string
  updated_at: string
}

export const auditLogsApi = {
  list: async (): Promise<AuditLogResponse[]> => {
    const response = await api.get('/audit-logs/')
    return response.data
  },
}
