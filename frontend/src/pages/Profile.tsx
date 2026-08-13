import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { getErrorMessage } from '../utils/errors'
import { inputClass } from '../components/FormField'

const MIN_PASSWORD = 8

const Profile = () => {
  const { user, updateProfile, changePassword } = useAuth()
  const [profileForm, setProfileForm] = useState({
    email: '',
    username: '',
    full_name: '',
  })
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  })
  const [profileMessage, setProfileMessage] = useState('')
  const [profileError, setProfileError] = useState('')
  const [passwordMessage, setPasswordMessage] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [savingProfile, setSavingProfile] = useState(false)
  const [savingPassword, setSavingPassword] = useState(false)
  const [showPasswords, setShowPasswords] = useState(false)

  useEffect(() => {
    if (user) {
      setProfileForm({
        email: user.email,
        username: user.username,
        full_name: user.full_name,
      })
    }
  }, [user])

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setProfileError('')
    setProfileMessage('')
    setSavingProfile(true)
    try {
      await updateProfile(profileForm)
      setProfileMessage('Datos actualizados correctamente')
    } catch (err) {
      setProfileError(getErrorMessage(err, 'No se pudo actualizar el perfil'))
    } finally {
      setSavingProfile(false)
    }
  }

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setPasswordError('')
    setPasswordMessage('')

    if (passwordForm.new_password.length < MIN_PASSWORD) {
      setPasswordError(`La nueva contraseña debe tener al menos ${MIN_PASSWORD} caracteres`)
      return
    }
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setPasswordError('Las contraseñas nuevas no coinciden')
      return
    }
    if (passwordForm.new_password === passwordForm.current_password) {
      setPasswordError('La nueva contraseña debe ser distinta a la actual')
      return
    }

    setSavingPassword(true)
    try {
      await changePassword({
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
      })
      setPasswordForm({
        current_password: '',
        new_password: '',
        confirm_password: '',
      })
      setPasswordMessage('Contraseña actualizada correctamente')
    } catch (err) {
      setPasswordError(getErrorMessage(err, 'No se pudo cambiar la contraseña'))
    } finally {
      setSavingPassword(false)
    }
  }

  const passwordType = showPasswords ? 'text' : 'password'
  const newLen = passwordForm.new_password.length
  const passwordHint =
    newLen === 0
      ? `Mínimo ${MIN_PASSWORD} caracteres`
      : newLen < MIN_PASSWORD
        ? `Faltan ${MIN_PASSWORD - newLen} caracteres`
        : 'Longitud OK'

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Mi cuenta</h2>
        <p className="text-gray-600">
          Editá tus datos y cambiá la contraseña. Si olvidaste la clave, usá{' '}
          <Link to="/recover-password" className="text-blue-600 hover:underline">
            recuperar contraseña
          </Link>
          .
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <form onSubmit={handleProfileSubmit} className="bg-white shadow rounded-lg p-6 space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Datos de perfil</h3>
          {profileMessage && (
            <div className="p-3 rounded-md bg-emerald-50 text-emerald-800 text-sm">{profileMessage}</div>
          )}
          {profileError && <div className="p-3 rounded-md bg-red-50 text-red-700 text-sm">{profileError}</div>}
          <div>
            <label htmlFor="profile-full-name" className="block text-sm font-medium text-gray-700">
              Nombre completo
            </label>
            <input
              id="profile-full-name"
              className={`mt-1 ${inputClass}`}
              required
              minLength={1}
              value={profileForm.full_name}
              onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
            />
          </div>
          <div>
            <label htmlFor="profile-username" className="block text-sm font-medium text-gray-700">
              Usuario
            </label>
            <input
              id="profile-username"
              className={`mt-1 ${inputClass}`}
              required
              minLength={3}
              value={profileForm.username}
              onChange={(e) => setProfileForm({ ...profileForm, username: e.target.value })}
            />
          </div>
          <div>
            <label htmlFor="profile-email" className="block text-sm font-medium text-gray-700">
              Correo electrónico
            </label>
            <input
              id="profile-email"
              type="email"
              className={`mt-1 ${inputClass}`}
              required
              value={profileForm.email}
              onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
            />
          </div>
          <div className="text-xs text-gray-500">
            Tenant: {user?.tenant_id?.slice(0, 8)}… · Company: {user?.company_id?.slice(0, 8)}…
          </div>
          <button
            type="submit"
            disabled={savingProfile}
            className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {savingProfile ? 'Guardando...' : 'Guardar cambios'}
          </button>
        </form>

        <form onSubmit={handlePasswordSubmit} className="bg-white shadow rounded-lg p-6 space-y-4">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-lg font-semibold text-gray-900">Cambiar contraseña</h3>
            <label className="flex items-center gap-1.5 text-xs text-gray-600">
              <input
                type="checkbox"
                checked={showPasswords}
                onChange={(e) => setShowPasswords(e.target.checked)}
              />
              Mostrar
            </label>
          </div>
          {passwordMessage && (
            <div className="p-3 rounded-md bg-emerald-50 text-emerald-800 text-sm">{passwordMessage}</div>
          )}
          {passwordError && <div className="p-3 rounded-md bg-red-50 text-red-700 text-sm">{passwordError}</div>}
          <div>
            <label htmlFor="pwd-current" className="block text-sm font-medium text-gray-700">
              Contraseña actual
            </label>
            <input
              id="pwd-current"
              type={passwordType}
              className={`mt-1 ${inputClass}`}
              required
              minLength={MIN_PASSWORD}
              autoComplete="current-password"
              value={passwordForm.current_password}
              onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
            />
          </div>
          <div>
            <label htmlFor="pwd-new" className="block text-sm font-medium text-gray-700">
              Nueva contraseña
            </label>
            <input
              id="pwd-new"
              type={passwordType}
              className={`mt-1 ${inputClass}`}
              required
              minLength={MIN_PASSWORD}
              autoComplete="new-password"
              value={passwordForm.new_password}
              onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
            />
            <p className={`mt-1 text-xs ${newLen > 0 && newLen < MIN_PASSWORD ? 'text-amber-700' : 'text-gray-500'}`}>
              {passwordHint}
            </p>
          </div>
          <div>
            <label htmlFor="pwd-confirm" className="block text-sm font-medium text-gray-700">
              Confirmar nueva contraseña
            </label>
            <input
              id="pwd-confirm"
              type={passwordType}
              className={`mt-1 ${inputClass}`}
              required
              minLength={MIN_PASSWORD}
              autoComplete="new-password"
              value={passwordForm.confirm_password}
              onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
            />
          </div>
          <button
            type="submit"
            disabled={savingPassword}
            className="rounded-md bg-gray-900 px-4 py-2 text-white hover:bg-gray-800 disabled:opacity-50"
          >
            {savingPassword ? 'Cambiando...' : 'Cambiar contraseña'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default Profile
