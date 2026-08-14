interface FormFieldProps {
  label: string
  children: React.ReactNode
}

export const inputClass =
  'mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-[#1E293B] shadow-sm placeholder:text-slate-400 focus:border-[#247BA0] focus:outline-none focus:ring-2 focus:ring-[#3E92CC]/40'

const FormField = ({ label, children }: FormFieldProps) => (
  <div>
    <label className="block text-sm font-medium text-[#1E293B]">{label}</label>
    {children}
  </div>
)

export default FormField
