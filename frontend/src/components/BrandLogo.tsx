type BrandLogoProps = {
  /** Visual size preset */
  size?: 'sm' | 'md' | 'lg'
  className?: string
  /** Hide decorative wordmark context when logo already includes text */
  alt?: string
}

const sizeClass: Record<NonNullable<BrandLogoProps['size']>, string> = {
  sm: 'h-[4.5rem] w-auto',
  md: 'h-16 w-auto',
  lg: 'h-36 w-auto max-w-[300px]',
}

/** Official mark from docs/Nexorux-erp.png (served as /Nexorux-erp.png). */
const BrandLogo = ({ size = 'md', className = '', alt = 'Nexorux ERP' }: BrandLogoProps) => (
  <img
    src="/Nexorux-erp.png"
    alt={alt}
    className={`${sizeClass[size]} object-contain ${className}`.trim()}
    decoding="async"
  />
)

export default BrandLogo
