import type { IconProps } from '~/types/common'

export default function SearchIcon(props: Readonly<IconProps>) {
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
        d="M17.5 17.5l-3.625-3.625m1.958-4.708a6.667 6.667 0 11-13.333 0 6.667 6.667 0 0113.333 0z"
        stroke="currentColor"
        strokeWidth={1.66667}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
