import { api } from './api'

export interface PurchaseReceiptItemCreate {
  product_id: string
  quantity: number
  unit_cost?: number
  description?: string
}

export interface PurchaseReceiptItemResponse {
  id: string
  tenant_id: string
  company_id: string
  receipt_id: string
  product_id?: string
  quantity: number
  unit_cost: number
  description?: string
  created_at: string
  updated_at: string
}

export interface PurchaseReceiptCreate {
  tenant_id: string
  company_id: string
  supplier_id: string
  warehouse_id: string
  number?: string
  receipt_date: string
  notes?: string
  items: PurchaseReceiptItemCreate[]
}

export interface PurchaseReceiptResponse {
  id: string
  tenant_id: string
  company_id: string
  supplier_id?: string
  warehouse_id?: string
  number: string
  receipt_date: string
  notes?: string
  status: string
  items: PurchaseReceiptItemResponse[]
  created_at: string
  updated_at: string
}

export const purchaseReceiptsApi = {
  list: async (): Promise<PurchaseReceiptResponse[]> => {
    const response = await api.get('/purchase-receipts/')
    return response.data
  },

  get: async (id: string): Promise<PurchaseReceiptResponse> => {
    const response = await api.get(`/purchase-receipts/${id}`)
    return response.data
  },

  create: async (data: PurchaseReceiptCreate): Promise<PurchaseReceiptResponse> => {
    const response = await api.post('/purchase-receipts/', data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/purchase-receipts/${id}`)
  },
}
