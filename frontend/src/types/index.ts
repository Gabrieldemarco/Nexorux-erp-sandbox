export interface Tenant {
  id: string
  name: string
  status: string
  settings: Record<string, any>
  created_at: string
  updated_at: string
}

export interface Company {
  id: string
  tenant_id: string
  legal_name: string
  trade_name?: string
  rut: string
  fiscal_address?: string
  phone?: string
  email?: string
  website?: string
  country: string
  department?: string
  locality?: string
  currency: string
  tax_regime?: string
  created_at: string
  updated_at: string
}

export interface User {
  id: string
  email: string
  username: string
  full_name: string
  tenant_id: string
  company_id: string
  is_active: boolean
  settings?: Record<string, any> | null
  created_at: string
  updated_at: string
}

export interface Product {
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

export interface Customer {
  id: string
  tenant_id: string
  company_id: string
  customer_type: string
  legal_name: string
  trade_name?: string
  rut: string
  document_type?: string
  address?: string
  email?: string
  phone?: string
  currency: string
  credit_limit: number
  payment_terms?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Supplier {
  id: string
  tenant_id: string
  company_id: string
  legal_name: string
  trade_name?: string
  rut: string
  document_type?: string
  address?: string
  email?: string
  phone?: string
  currency: string
  payment_terms?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Invoice {
  id: string
  tenant_id: string
  company_id: string
  customer_id?: string
  branch_id?: string
  warehouse_id?: string
  document_type: string
  series: string
  number: string
  status: string
  issue_date: string
  due_date: string
  subtotal: number
  tax_total: number
  discount_total: number
  total: number
  currency: string
  exchange_rate: number
  notes?: string
  created_at: string
  updated_at: string
}

export interface FiscalDocument {
  id: string
  tenant_id: string
  company_id: string
  invoice_id: string
  document_type: string
  series: string
  number: string
  state: string
  issued_at?: string
  signed_at?: string
  sent_at?: string
  response_at?: string
  is_contingency: boolean
  xml_reference?: string
  raw_payload?: Record<string, any>
  created_at: string
  updated_at: string
}
