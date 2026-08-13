import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import Profile from '../pages/Profile'
import { AuthProvider } from '../hooks/useAuth'
import { authApi } from '../services/auth'

vi.mock('../services/auth')

const mockUser = {
  id: '1',
  email: 'test@example.com',
  username: 'testuser',
  full_name: 'Test User',
  tenant_id: 'tenant-1',
  company_id: 'company-1',
  is_active: true,
}

const renderProfile = () =>
  render(
    <MemoryRouter>
      <AuthProvider>
        <Profile />
      </AuthProvider>
    </MemoryRouter>
  )

describe('Profile page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('access_token', 'token')
    vi.mocked(authApi.me).mockResolvedValue(mockUser as any)
    vi.mocked(authApi.updateMe).mockResolvedValue({
      ...mockUser,
      full_name: 'Nombre Actualizado',
    } as any)
    vi.mocked(authApi.changePassword).mockResolvedValue({ message: 'ok' })
  })

  it('loads profile and updates name', async () => {
    const user = userEvent.setup()
    renderProfile()

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test User')).toBeInTheDocument()
    })

    const nameInput = screen.getByDisplayValue('Test User')
    await user.clear(nameInput)
    await user.type(nameInput, 'Nombre Actualizado')
    await user.click(screen.getByRole('button', { name: /guardar cambios/i }))

    await waitFor(() => {
      expect(authApi.updateMe).toHaveBeenCalled()
      expect(screen.getByText(/datos actualizados correctamente/i)).toBeInTheDocument()
    })
  })

  it('rejects mismatched new passwords client-side', async () => {
    const user = userEvent.setup()
    renderProfile()

    await waitFor(() => {
      expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument()
    })

    await user.type(screen.getByLabelText(/^contraseña actual$/i), 'secret123')
    await user.type(screen.getByLabelText(/^nueva contraseña$/i), 'newpass99')
    await user.type(screen.getByLabelText(/^confirmar nueva contraseña$/i), 'otherpass')
    await user.click(screen.getByRole('button', { name: /^cambiar contraseña$/i }))

    expect(await screen.findByText(/no coinciden/i)).toBeInTheDocument()
    expect(authApi.changePassword).not.toHaveBeenCalled()
  })

  it('changes password when valid', async () => {
    const user = userEvent.setup()
    renderProfile()

    await waitFor(() => {
      expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument()
    })

    await user.type(screen.getByLabelText(/^contraseña actual$/i), 'secret123')
    await user.type(screen.getByLabelText(/^nueva contraseña$/i), 'newpass99')
    await user.type(screen.getByLabelText(/^confirmar nueva contraseña$/i), 'newpass99')
    await user.click(screen.getByRole('button', { name: /^cambiar contraseña$/i }))

    await waitFor(() => {
      expect(authApi.changePassword).toHaveBeenCalledWith({
        current_password: 'secret123',
        new_password: 'newpass99',
      })
      expect(screen.getByText(/contraseña actualizada correctamente/i)).toBeInTheDocument()
    })
  })
})
