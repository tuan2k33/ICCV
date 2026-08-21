import type { IconProps } from '~/types/common'

export default function CheckCheckboxIcon(props: Readonly<IconProps>) {
  return (
    <svg
      width="1em"
      height="1em"
      viewBox="0 0 12 12"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path
        d="M10 3L4.5 8.5 2 6"
        stroke="currentColor"
        strokeWidth={1.6666}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
