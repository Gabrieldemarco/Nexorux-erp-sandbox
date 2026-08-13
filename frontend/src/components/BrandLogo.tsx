type BrandLogoProps = {
  /** Visual size preset */
  size?: 'sm' | 'md' | 'lg'
  className?: string
  /** Hide decorative wordmark context when logo already includes text */
  alt?: string
}

const sizeClass: Record<NonNullable<BrandLogoProps['size']>, string> = {
  sm: 'h-8 w-auto',
  md: 'h-12 w-auto',
  lg: 'h-24 w-auto max-w-[220px]',
}

/** Nexorux brand mark from /nexorux-erp-logo.png (public). */
const BrandLogo = ({ size = 'md', className = '', alt = 'Nexorux ERP' }: BrandLogoProps) => (
  <img
    src="/nexorux-erp-logo.png"
    alt={alt}
    className={`${sizeClass[size]} object-contain ${className}`.trim()}
    decoding="async"
  />
)

export default BrandLogo
