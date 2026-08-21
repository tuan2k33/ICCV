import type { IconProps } from '~/types/common'

export default function RefreshIcon(props: IconProps) {
  return (
    <svg
      width="1em"
      height="1em"
      viewBox="0 0 20 20"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path
        d="M17.5 8.333S15.828 6.057 14.47 4.7a7.5 7.5 0 101.902 7.385m1.126-3.75v-5m0 5h-5"
        stroke="currentColor"
        strokeWidth={1.66667}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
