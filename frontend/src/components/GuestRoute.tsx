import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

interface GuestRouteProps {
  children: React.ReactNode
}

const GuestRoute = ({ children }: GuestRouteProps) => {
  const { token, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Cargando...</div>
      </div>
    )
  }

  if (token) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

export default GuestRoute
