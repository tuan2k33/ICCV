import type { IconProps } from '~/types/common'

export default function XCircleFilledIcon(props: Readonly<IconProps>) {
  return (
    <svg
      width="1em"
      height="1em"
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <g clipPath="url(#clip0_1289_20093)">
        <path d="M8 14.667A6.667 6.667 0 108 1.333a6.667 6.667 0 000 13.334z" fill="currentColor" />
        <path
          d="M10 6l-4 4m0-4l4 4m4.667-2A6.667 6.667 0 111.334 8a6.667 6.667 0 0113.333 0z"
          stroke="#fff"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </g>
      <defs>
        <clipPath id="clip0_1289_20093">
          <path fill="#fff" d="M0 0H16V16H0z" />
        </clipPath>
      </defs>
    </svg>
  )
}
