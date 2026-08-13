import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import Tenants from '../pages/Tenants'
import Invoices from '../pages/Invoices'
import { AuthProvider } from '../hooks/useAuth'
import { authApi } from '../services/auth'
import { tenantsApi } from '../services/tenants'
import { invoicesApi } from '../services/invoices'
import { customersApi } from '../services/customers'
import { productsApi } from '../services/products'
import { invoiceItemsApi } from '../services/invoiceItems'
import { branchesApi } from '../services/branches'
import { warehousesApi } from '../services/warehouses'

vi.mock('../services/auth')
vi.mock('../services/tenants')
vi.mock('../services/invoices')
vi.mock('../services/customers')
vi.mock('../services/products')
vi.mock('../services/invoiceItems')
vi.mock('../services/branches')
vi.mock('../services/warehouses')

const mockUser = {
  id: '1',
  email: 'test@example.com',
  username: 'test',
  full_name: 'Test User',
  tenant_id: 'tenant-1',
  company_id: 'company-1',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

const renderWithProviders = (ui: React.ReactElement) =>
  render(
    <MemoryRouter>
      <AuthProvider>{ui}</AuthProvider>
    </MemoryRouter>
  )

describe('Tenants CRUD', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('access_token', 'test-token')
    vi.mocked(authApi.me).mockResolvedValue(mockUser)
    vi.mocked(tenantsApi.list).mockResolvedValue([
      { id: 't1', name: 'Tenant Demo', status: 'active', settings: {}, created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z' },
    ])
    vi.mocked(tenantsApi.create).mockResolvedValue({
      id: 't2',
      name: 'Nuevo Tenant',
      status: 'active',
      settings: {},
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    })
    vi.mocked(tenantsApi.update).mockResolvedValue({
      id: 't1',
      name: 'Tenant Demo',
      status: 'active',
      settings: {},
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    })
    vi.mocked(tenantsApi.delete).mockResolvedValue()
  })

  it('renders tenant list', async () => {
    renderWithProviders(<Tenants />)
    expect(await screen.findByText('Tenant Demo')).toBeInTheDocument()
  })

  it('creates a tenant', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Tenants />)
    await screen.findByText('Tenant Demo')

    await user.click(screen.getByRole('button', { name: /agregar tenant/i }))
    await user.type(screen.getAllByRole('textbox')[0], 'Nuevo Tenant')
    await user.click(screen.getByRole('button', { name: /guardar/i }))

    await waitFor(() => {
      expect(tenantsApi.create).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'Nuevo Tenant', status: 'active' })
      )
    })
  })
})

describe('Invoices CRUD', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('access_token', 'test-token')
    vi.mocked(authApi.me).mockResolvedValue(mockUser)
    vi.mocked(invoicesApi.list).mockResolvedValue([
      {
        id: 'inv-1',
        tenant_id: 'tenant-1',
        company_id: 'company-1',
        customer_id: 'cust-1',
        branch_id: 'branch-1',
        warehouse_id: 'wh-1',
        document_type: '111',
        series: 'A',
        number: '0001',
        status: 'draft',
        issue_date: '2024-01-01T00:00:00',
        due_date: '2024-01-31T00:00:00',
        subtotal: 100,
        tax_total: 22,
        discount_total: 0,
        total: 122,
        currency: 'UYU',
        exchange_rate: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ])
    vi.mocked(customersApi.list).mockResolvedValue([
      { id: 'cust-1', tenant_id: 'tenant-1', company_id: 'company-1', customer_type: 'company', legal_name: 'Cliente Test', rut: '123', currency: 'UYU', credit_limit: 0, is_active: true, created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z' },
      { id: 'cust-cf', tenant_id: 'tenant-1', company_id: 'company-1', customer_type: 'final_consumer', legal_name: 'Consumidor Final', rut: '00000000', currency: 'UYU', credit_limit: 0, is_active: true, created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z' },
    ])
    vi.mocked(productsApi.list).mockResolvedValue([
      {
        id: 'prod-1',
        tenant_id: 'tenant-1',
        company_id: 'company-1',
        name: 'Producto Demo',
        sku: 'DEMO-001',
        barcode: '7790001000111',
        product_type: 'good',
        unit_of_measure: 'unit',
        sales_price: 100,
        cost_price: 50,
        tax_rate: 22,
        is_service: false,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
      {
        id: 'prod-2',
        tenant_id: 'tenant-1',
        company_id: 'company-1',
        name: 'Café Premium',
        sku: 'CAFE-100',
        barcode: '7790002000222',
        product_type: 'good',
        unit_of_measure: 'unit',
        sales_price: 250,
        cost_price: 120,
        tax_rate: 22,
        is_service: false,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ])
    vi.mocked(invoiceItemsApi.list).mockResolvedValue([])
    vi.mocked(branchesApi.list).mockResolvedValue([
      { id: 'branch-1', tenant_id: 'tenant-1', company_id: 'company-1', name: 'Sucursal Central', code: 'SC', is_active: true, created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z' },
    ])
    vi.mocked(warehousesApi.list).mockResolvedValue([
      { id: 'wh-1', tenant_id: 'tenant-1', company_id: 'company-1', name: 'Depósito Principal', code: 'DP', is_active: true, created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z' },
    ])
    vi.mocked(invoicesApi.create).mockResolvedValue({} as never)
    vi.mocked(invoicesApi.delete).mockResolvedValue()
  })

  it('renders invoice list with readable CFE type label', async () => {
    renderWithProviders(<Invoices />)
    expect(await screen.findByText('A-0001')).toBeInTheDocument()
    expect(screen.getByText('e-Factura (111)')).toBeInTheDocument()
  })

  it('opens create invoice modal with references', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Invoices />)
    await screen.findByText('A-0001')

    await user.click(screen.getByRole('button', { name: /agregar factura/i }))

    expect(await screen.findByRole('heading', { name: /agregar factura/i })).toBeInTheDocument()
    await waitFor(() => {
      expect(customersApi.list).toHaveBeenCalled()
      expect(productsApi.list).toHaveBeenCalled()
    })
    await waitFor(() => {
      expect(screen.queryByText(/Cargando referencias/i)).not.toBeInTheDocument()
    })
    expect(screen.getByText(/Detalle de productos/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /fila manual/i })).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Escaneá o escribí y Enter/i)).toBeInTheDocument()
  })

  it('adds a line by barcode scan and increments on second scan', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Invoices />)
    await screen.findByText('A-0001')
    await user.click(screen.getByRole('button', { name: /agregar factura/i }))
    await waitFor(() => {
      expect(screen.queryByText(/Cargando referencias/i)).not.toBeInTheDocument()
    })

    const scan = screen.getByPlaceholderText(/Escaneá o escribí y Enter/i)
    await user.type(scan, '7790001000111')
    await user.click(screen.getByRole('button', { name: /^agregar$/i }))

    expect(await screen.findByText('+ Producto Demo')).toBeInTheDocument()
    const qtyInputs = screen.getAllByDisplayValue('1')
    expect(qtyInputs.length).toBeGreaterThan(0)

    await user.type(scan, 'DEMO-001')
    await user.keyboard('{Enter}')

    expect(await screen.findByDisplayValue('2')).toBeInTheDocument()
  })

  it('shows product suggestions while typing a name', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Invoices />)
    await screen.findByText('A-0001')
    await user.click(screen.getByRole('button', { name: /agregar factura/i }))
    await waitFor(() => {
      expect(screen.queryByText(/Cargando referencias/i)).not.toBeInTheDocument()
    })

    await user.type(screen.getByPlaceholderText(/Escaneá o escribí y Enter/i), 'café')
    expect(await screen.findByRole('button', { name: /Café Premium/i })).toBeInTheDocument()
  })

  it('shows not-found message for unknown scan codes', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Invoices />)
    await screen.findByText('A-0001')
    await user.click(screen.getByRole('button', { name: /agregar factura/i }))
    await waitFor(() => {
      expect(screen.queryByText(/Cargando referencias/i)).not.toBeInTheDocument()
    })

    await user.type(screen.getByPlaceholderText(/Escaneá o escribí y Enter/i), 'NO-EXISTE')
    await user.click(screen.getByRole('button', { name: /^agregar$/i }))

    expect(await screen.findByText(/No se encontró: NO-EXISTE/i)).toBeInTheDocument()
  })
})
