import { api } from './api'

export interface ProductResponse {
  id: string
  tenant_id: string
  company_id: string
  name: string
  sku: string
  barcode?: string
  description?: string
  product_type: string
  unit_of_measure: string
  sales_price: number
  cost_price: number
  tax_rate: number
  is_service: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ProductCreate {
  tenant_id: string
  company_id: string
  name: string
  sku: string
  barcode?: string
  description?: string
  product_type?: string
  unit_of_measure?: string
  sales_price: number
  cost_price: number
  tax_rate?: number
  is_service?: boolean
  is_active?: boolean
}

export interface ProductUpdate {
  name?: string
  sku?: string
  barcode?: string
  description?: string
  product_type?: string
  unit_of_measure?: string
  sales_price?: number
  cost_price?: number
  tax_rate?: number
  is_service?: boolean
  is_active?: boolean
}

export const productsApi = {
  list: async (): Promise<ProductResponse[]> => {
    const response = await api.get('/products/')
    return response.data
  },

  get: async (id: string): Promise<ProductResponse> => {
    const response = await api.get(`/products/${id}`)
    return response.data
  },

  create: async (data: ProductCreate): Promise<ProductResponse> => {
    const response = await api.post('/products/', data)
    return response.data
  },

  update: async (id: string, data: ProductUpdate): Promise<ProductResponse> => {
    const response = await api.put(`/products/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/products/${id}`)
  },
}
