import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import Register from '../pages/Register'
import { AuthProvider } from '../hooks/useAuth'
import { authApi } from '../services/auth'

vi.mock('../services/auth')

const renderRegister = () =>
  render(
    <MemoryRouter>
      <AuthProvider>
        <Register />
      </AuthProvider>
    </MemoryRouter>
  )

const fillBaseFields = async (user: ReturnType<typeof userEvent.setup>) => {
  await user.type(screen.getByPlaceholderText('Nombre completo'), 'Nuevo Usuario')
  await user.type(screen.getByPlaceholderText('Correo electrónico'), 'nuevo@example.com')
  await user.type(screen.getByPlaceholderText('Usuario'), 'nuevo')
  await user.type(screen.getByPlaceholderText('Contraseña (mín. 8)'), 'password1')
}

describe('Register', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    vi.mocked(authApi.register).mockResolvedValue({
      id: '1',
      email: 'nuevo@example.com',
      username: 'nuevo',
      full_name: 'Nuevo Usuario',
      tenant_id: 'tenant-new',
      company_id: 'company-new',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    })
    vi.mocked(authApi.login).mockResolvedValue({
      access_token: 'token',
      refresh_token: 'refresh',
      token_type: 'bearer',
    })
    vi.mocked(authApi.me).mockResolvedValue({
      id: '1',
      email: 'nuevo@example.com',
      username: 'nuevo',
      full_name: 'Nuevo Usuario',
      tenant_id: 'tenant-new',
      company_id: 'company-new',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    })
  })

  it('registers creating a new organization by default', async () => {
    const user = userEvent.setup()
    renderRegister()

    expect(screen.getByText(/crear organización nueva/i)).toBeInTheDocument()
    expect(screen.queryByPlaceholderText('uuid del tenant')).not.toBeInTheDocument()

    await fillBaseFields(user)
    await user.click(screen.getByRole('button', { name: /registrarse/i }))

    await waitFor(() => {
      expect(authApi.register).toHaveBeenCalledWith({
        email: 'nuevo@example.com',
        username: 'nuevo',
        full_name: 'Nuevo Usuario',
        password: 'password1',
      })
    })
  })

  it('requires tenant and company UUIDs when joining an org', async () => {
    const user = userEvent.setup()
    renderRegister()

    await user.click(screen.getByText(/unirme a organización existente/i))
    expect(screen.getByPlaceholderText('uuid del tenant')).toBeInTheDocument()

    await fillBaseFields(user)
    await user.click(screen.getByRole('button', { name: /registrarse/i }))

    expect(
      await screen.findByText(/indicá tenant y razón social \(UUID\)/i)
    ).toBeInTheDocument()
    expect(authApi.register).not.toHaveBeenCalled()
  })

  it('registers joining an existing organization with UUIDs', async () => {
    const user = userEvent.setup()
    renderRegister()

    await user.click(screen.getByText(/unirme a organización existente/i))
    await fillBaseFields(user)
    await user.type(screen.getByPlaceholderText('uuid del tenant'), 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee')
    await user.type(
      screen.getByPlaceholderText('uuid de la razón social'),
      '11111111-2222-3333-4444-555555555555'
    )
    await user.click(screen.getByRole('button', { name: /registrarse/i }))

    await waitFor(() => {
      expect(authApi.register).toHaveBeenCalledWith({
        email: 'nuevo@example.com',
        username: 'nuevo',
        full_name: 'Nuevo Usuario',
        password: 'password1',
        tenant_id: 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
        company_id: '11111111-2222-3333-4444-555555555555',
      })
    })
  })
})
