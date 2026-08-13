import { api } from './api'

export interface PriceListResponse {
  id: string
  tenant_id: string
  company_id: string
  name: string
  currency: string
  valid_from?: string | null
  valid_to?: string | null
  is_default?: boolean
  created_at: string
  updated_at: string
}

export interface PriceListCreate {
  tenant_id: string
  company_id: string
  name: string
  currency: string
  valid_from?: string
  valid_to?: string
  is_default?: boolean
}

export interface PriceListUpdate {
  name?: string
  currency?: string
  valid_from?: string
  valid_to?: string
  is_default?: boolean
}

export const priceListsApi = {
  list: async (): Promise<PriceListResponse[]> => {
    const response = await api.get('/price-lists/')
    return response.data
  },

  get: async (id: string): Promise<PriceListResponse> => {
    const response = await api.get(`/price-lists/${id}`)
    return response.data
  },

  create: async (data: PriceListCreate): Promise<PriceListResponse> => {
    const response = await api.post('/price-lists/', data)
    return response.data
  },

  update: async (id: string, data: PriceListUpdate): Promise<PriceListResponse> => {
    const response = await api.put(`/price-lists/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/price-lists/${id}`)
  },
}
