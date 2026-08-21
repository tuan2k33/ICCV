import type { IconProps } from '~/types/common'

export default function CheckCircleIcon(props: Readonly<IconProps>) {
  return (
    <svg
      width="1em"
      height="1em"
      viewBox="0 0 20 20"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <g clipPath="url(#clip0_1350_12929)">
        <path
          d="M6.25 10l2.5 2.5 5-5m4.583 2.5a8.333 8.333 0 11-16.667 0 8.333 8.333 0 0116.667 0z"
          stroke="currentColor"
          strokeWidth={1.66667}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </g>
      <defs>
        <clipPath id="clip0_1350_12929">
          <path fill="#fff" d="M0 0H20V20H0z" />
        </clipPath>
      </defs>
    </svg>
  )
}
