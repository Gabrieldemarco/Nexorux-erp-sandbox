import { api } from './api'

export interface StockMovementResponse {
  id: string
  tenant_id: string
  company_id: string
  warehouse_id: string
  product_id: string
  quantity: number
  movement_type: string
  reference_id?: string
  reference_type?: string
  movement_date: string
  created_at: string
  updated_at: string
}

export interface StockMovementCreate {
  tenant_id: string
  company_id: string
  warehouse_id?: string
  product_id?: string
  quantity: number
  movement_type: string
  reference_id?: string
  reference_type?: string
  movement_date: string
}

export interface StockMovementUpdate {
  quantity?: number
  movement_type?: string
  reference_id?: string
  reference_type?: string
  movement_date?: string
  warehouse_id?: string
  product_id?: string
}

export interface StockBalanceRow {
  product_id: string
  warehouse_id: string
  quantity: number
}

export const stockMovementsApi = {
  list: async (): Promise<StockMovementResponse[]> => {
    const response = await api.get('/stock-movements/')
    return response.data
  },

  balances: async (params?: {
    warehouse_id?: string
    product_id?: string
  }): Promise<StockBalanceRow[]> => {
    const response = await api.get('/stock-movements/balances', { params })
    return response.data
  },

  get: async (id: string): Promise<StockMovementResponse> => {
    const response = await api.get(`/stock-movements/${id}`)
    return response.data
  },

  create: async (data: StockMovementCreate): Promise<StockMovementResponse> => {
    const response = await api.post('/stock-movements/', data)
    return response.data
  },

  update: async (id: string, data: StockMovementUpdate): Promise<StockMovementResponse> => {
    const response = await api.put(`/stock-movements/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/stock-movements/${id}`)
  },
}
