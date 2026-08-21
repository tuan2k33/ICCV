import type { IconProps } from '~/types/common'

export default function PlusCircleIcon(props: Readonly<IconProps>) {
  return (
    <svg
      width="1em"
      height="1em"
      viewBox="0 0 24 25"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path
        d="M12.0001 8.5V16.5M8.00012 12.5H16.0001M22.0001 12.5C22.0001 18.0228 17.523 22.5 12.0001 22.5C6.47727 22.5 2.00012 18.0228 2.00012 12.5C2.00012 6.97715 6.47727 2.5 12.0001 2.5C17.523 2.5 22.0001 6.97715 22.0001 12.5Z"
        stroke="currentColor"
        strokeWidth="1.66667"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
