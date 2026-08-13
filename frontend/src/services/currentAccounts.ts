import { api } from './api'

export interface CurrentAccountInvoiceLine {
  invoice_id: string
  series: string
  number: string
  document_type: string
  status: string
  issue_date?: string | null
  due_date?: string | null
  currency: string
  total: number
  signed_total: number
  paid_amount: number
  balance: number
  overdue: boolean
}

export interface CurrentAccountPaymentLine {
  payment_id: string
  payment_date: string
  amount: number
  currency: string
  payment_method: string
  reference?: string | null
  status: string
  invoice_id?: string | null
}

export interface CurrentAccountBalance {
  customer_id: string
  legal_name: string
  trade_name?: string | null
  rut: string
  currency: string
  is_active: boolean
  credit_limit: number
  invoiced: number
  paid: number
  balance: number
  available_credit?: number | null
  overdue: number
  open_invoices: number
}

export interface CurrentAccountStatement extends CurrentAccountBalance {
  invoices: CurrentAccountInvoiceLine[]
  payments: CurrentAccountPaymentLine[]
}

export const currentAccountsApi = {
  list: async (): Promise<CurrentAccountBalance[]> => {
    const response = await api.get('/current-accounts/')
    return response.data
  },

  get: async (customerId: string): Promise<CurrentAccountStatement> => {
    const response = await api.get(`/current-accounts/${customerId}`)
    return response.data
  },
}
