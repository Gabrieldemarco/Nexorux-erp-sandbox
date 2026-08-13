import { createContext, useContext, useEffect, useState } from 'react'
import { authApi } from '../services/auth'
import type { UserProfileUpdateRequest, ChangePasswordRequest } from '../services/auth'

interface User {
  id: string
  email: string
  username: string
  full_name: string
  tenant_id: string
  company_id: string
  is_active: boolean
  settings?: Record<string, any> | null
  permission_codes?: string[]
  role_keys?: string[]
}

interface AuthContextType {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: any) => Promise<void>
  refreshUser: () => Promise<User>
  updateProfile: (data: UserProfileUpdateRequest) => Promise<User>
  changePassword: (data: ChangePasswordRequest) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(localStorage.getItem('access_token'))
  const [loading, setLoading] = useState(true)

  const refreshUser = async () => {
    const user = await authApi.me()
    setUser(user)
    return user
  }

  useEffect(() => {
    if (token) {
      refreshUser()
        .catch((err) => {
          console.error('Failed to fetch current user:', err)
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          setToken(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [token])

  const login = async (email: string, password: string) => {
    const response = await authApi.login({ email, password })
    localStorage.setItem('access_token', response.access_token)
    localStorage.setItem('refresh_token', response.refresh_token)
    setToken(response.access_token)
    const user = await authApi.me()
    setUser(user)
  }

  const register = async (data: any) => {
    await authApi.register(data)
    await login(data.email, data.password)
  }

  const updateProfile = async (data: UserProfileUpdateRequest) => {
    const updatedUser = await authApi.updateMe(data)
    setUser(updatedUser)
    return updatedUser
  }

  const changePassword = async (data: ChangePasswordRequest) => {
    await authApi.changePassword(data)
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, refreshUser, updateProfile, changePassword, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
