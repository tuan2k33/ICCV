import React from 'react'
import type { IconProps } from '~/types/common'

export default function PlayIcon(props: Readonly<IconProps>) {
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
        d="M4.16663 4.15809C4.16663 3.34879 4.16663 2.94414 4.33537 2.72108C4.48237 2.52675 4.70706 2.4065 4.95029 2.39198C5.22949 2.37531 5.56618 2.59977 6.23956 3.04869L15.0025 8.89067C15.5589 9.2616 15.8371 9.44707 15.9341 9.68084C16.0188 9.88522 16.0188 10.1149 15.9341 10.3193C15.8371 10.5531 15.5589 10.7385 15.0025 11.1095L6.23956 16.9514C5.56618 17.4004 5.22949 17.6248 4.95029 17.6082C4.70706 17.5936 4.48237 17.4734 4.33537 17.2791C4.16663 17.056 4.16663 16.6513 4.16663 15.842V4.15809Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
