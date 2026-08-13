interface FormFieldProps {
  label: string
  children: React.ReactNode
}

export const inputClass =
  'mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 sm:text-sm'

const FormField = ({ label, children }: FormFieldProps) => (
  <div>
    <label className="block text-sm font-medium text-gray-700">{label}</label>
    {children}
  </div>
)

export default FormField
