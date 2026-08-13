import { api } from './api'

export interface TaxConfigurationResponse {
  id: string
  tenant_id: string
  company_id: string
  tax_code: string
  description?: string | null
  rate: number
  effective_from?: string | null
  effective_to?: string | null
  metadata?: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface TaxConfigurationCreate {
  tenant_id: string
  company_id: string
  tax_code: string
  description?: string
  rate: number
  effective_from?: string
  effective_to?: string
  metadata?: Record<string, unknown>
}

export interface TaxConfigurationUpdate {
  tax_code?: string
  description?: string
  rate?: number
  effective_from?: string
  effective_to?: string
  metadata?: Record<string, unknown>
}

export const taxConfigurationsApi = {
  list: async (): Promise<TaxConfigurationResponse[]> => {
    const response = await api.get('/tax-configurations/')
    return response.data
  },

  get: async (id: string): Promise<TaxConfigurationResponse> => {
    const response = await api.get(`/tax-configurations/${id}`)
    return response.data
  },

  create: async (data: TaxConfigurationCreate): Promise<TaxConfigurationResponse> => {
    const response = await api.post('/tax-configurations/', data)
    return response.data
  },

  update: async (id: string, data: TaxConfigurationUpdate): Promise<TaxConfigurationResponse> => {
    const response = await api.put(`/tax-configurations/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/tax-configurations/${id}`)
  },
}
