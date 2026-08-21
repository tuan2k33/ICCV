import type { IconProps } from '~/types/common'

export default function FlagIcon(props: Readonly<IconProps>) {
  return (
    <svg
      width="1em"
      height="1em"
      viewBox="0 0 20 21"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path
        d="M3.33337 12.9998C3.33337 12.9998 4.16671 12.1665 6.66671 12.1665C9.16671 12.1665 10.8334 13.8332 13.3334 13.8332C15.8334 13.8332 16.6667 12.9998 16.6667 12.9998V2.99984C16.6667 2.99984 15.8334 3.83317 13.3334 3.83317C10.8334 3.83317 9.16671 2.1665 6.66671 2.1665C4.16671 2.1665 3.33337 2.99984 3.33337 2.99984L3.33337 18.8332"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
