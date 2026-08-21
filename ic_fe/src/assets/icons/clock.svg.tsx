import type { IconProps } from '~/types/common'

export default function ClockIcon(props: Readonly<IconProps>) {
  return (
    <svg
      width="1em"
      height="1em"
      viewBox="0 0 17 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path
        d="M8.50004 6.3335V9.00016L10.1667 10.0002M8.50004 3.3335C5.37043 3.3335 2.83337 5.87055 2.83337 9.00016C2.83337 12.1298 5.37043 14.6668 8.50004 14.6668C11.6297 14.6668 14.1667 12.1298 14.1667 9.00016C14.1667 5.87055 11.6297 3.3335 8.50004 3.3335ZM8.50004 3.3335V1.3335M7.16671 1.3335H9.83337M14.0527 3.72819L13.0527 2.72819L13.5527 3.22819M2.94739 3.72819L3.94739 2.72819L3.44739 3.22819"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
