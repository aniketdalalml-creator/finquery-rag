type LogoProps = {
  className?: string
  size?: number
}

export function Logo({ className = '', size = 32 }: LogoProps) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <rect width="32" height="32" rx="8" fill="#4AFF94" />
      <path
        d="M8 10h10a4 4 0 0 1 0 8H12v4H8V10zm4 3v2h6a1 1 0 0 0 0-2h-6z"
        fill="#00210D"
      />
      <circle cx="22" cy="22" r="5" stroke="#00210D" strokeWidth="2" fill="none" />
      <path
        d="M25.5 25.5L28 28"
        stroke="#00210D"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  )
}
