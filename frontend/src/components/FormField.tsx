interface FormFieldProps {
  label: string
  children: React.ReactNode
}

export const inputClass =
  'mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm placeholder:text-slate-400 focus:border-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-600/20'

const FormField = ({ label, children }: FormFieldProps) => (
  <div>
    <label className="block text-sm font-medium text-slate-700">{label}</label>
    {children}
  </div>
)

export default FormField
