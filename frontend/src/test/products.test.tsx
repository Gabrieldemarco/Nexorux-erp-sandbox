import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import Products from '../pages/Products'
import { AuthProvider } from '../hooks/useAuth'
import { authApi } from '../services/auth'
import { productsApi } from '../services/products'

vi.mock('../services/auth')
vi.mock('../services/products')

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

const mockProduct = {
  id: 'prod-1',
  tenant_id: 'tenant-1',
  company_id: 'company-1',
  name: 'Producto Test',
  sku: 'SKU-001',
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
}

const renderProducts = () =>
  render(
    <MemoryRouter>
      <AuthProvider>
        <Products />
      </AuthProvider>
    </MemoryRouter>
  )

describe('Products CRUD', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('access_token', 'test-token')
    vi.mocked(authApi.me).mockResolvedValue(mockUser)
    vi.mocked(productsApi.list).mockResolvedValue([mockProduct])
    vi.mocked(productsApi.create).mockResolvedValue(mockProduct)
    vi.mocked(productsApi.update).mockResolvedValue(mockProduct)
    vi.mocked(productsApi.delete).mockResolvedValue()
  })

  it('renders product list', async () => {
    renderProducts()
    expect(await screen.findByText('Producto Test')).toBeInTheDocument()
    expect(screen.getByText('SKU-001')).toBeInTheDocument()
    expect(screen.getByText('7790001000111')).toBeInTheDocument()
  })

  it('opens create modal and submits form with barcode', async () => {
    const user = userEvent.setup()
    renderProducts()
    await screen.findByText('Producto Test')

    await user.click(screen.getByRole('button', { name: /agregar producto/i }))
    expect(screen.getByRole('heading', { name: /agregar producto/i })).toBeInTheDocument()
    expect(screen.getByText('Código de barras')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('EAN / UPC / interno')).toBeInTheDocument()

    await user.type(screen.getAllByRole('textbox')[0], 'Nuevo Producto')
    await user.type(screen.getAllByRole('textbox')[1], 'SKU-NEW')
    await user.type(screen.getByPlaceholderText('EAN / UPC / interno'), '7791234567890')
    await user.click(screen.getByRole('button', { name: /guardar/i }))

    await waitFor(() => {
      expect(productsApi.create).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'Nuevo Producto',
          sku: 'SKU-NEW',
          barcode: '7791234567890',
          tenant_id: 'tenant-1',
          company_id: 'company-1',
        })
      )
    })
  })

  it('deletes a product after confirmation', async () => {
    const user = userEvent.setup()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    renderProducts()
    await screen.findByText('Producto Test')

    await user.click(screen.getByRole('button', { name: /^eliminar$/i }))

    await waitFor(() => {
      expect(productsApi.delete).toHaveBeenCalledWith('prod-1')
    })
  })
})
