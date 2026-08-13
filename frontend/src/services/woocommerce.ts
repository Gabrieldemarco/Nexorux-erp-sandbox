import { api } from './api'

export interface WooProductSyncItem {
  sku: string
  name?: string
  regular_price?: number | string
  price?: number | string
  barcode?: string
}

export interface WooProductSyncResult {
  dry_run: boolean
  created: number
  updated: number
  skipped: number
  total: number
  detail?: string | null
}

export interface WooOrderItem {
  id: string
  series: string
  number: string
  total: number
  status: string
  woocommerce_order_id?: string | number | null
  woocommerce_status?: string | null
  woocommerce_order_number?: string | null
}

export interface WooStockSyncItem {
  product_id: string
  sku: string
  name: string
  stock_quantity: number
}

export interface WooStockSyncResult {
  dry_run: boolean
  pushed: boolean
  configured: boolean
  updated: number
  skipped: number
  failed: number
  total: number
  items: WooStockSyncItem[]
  details?: Array<Record<string, unknown>>
  detail?: string | null
}

export const woocommerceApi = {
  syncProducts: async (
    products: WooProductSyncItem[],
    options?: { dry_run?: boolean }
  ): Promise<WooProductSyncResult> => {
    const response = await api.post('/integrations/woocommerce/sync/products', {
      dry_run: options?.dry_run ?? false,
      products,
    })
    return response.data
  },

  syncStock: async (options?: {
    dry_run?: boolean
    push?: boolean
    warehouse_id?: string
  }): Promise<WooStockSyncResult> => {
    const response = await api.post('/integrations/woocommerce/sync/stock', {
      dry_run: options?.dry_run ?? false,
      push: options?.push ?? true,
      warehouse_id: options?.warehouse_id || undefined,
    })
    return response.data
  },

  listOrders: async (): Promise<WooOrderItem[]> => {
    const response = await api.get('/integrations/woocommerce/orders')
    return response.data
  },
}
