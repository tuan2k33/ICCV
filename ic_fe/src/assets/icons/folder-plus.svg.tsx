import type { IconProps } from '~/types/common'

export default function FolderPlusIcon(props: Readonly<IconProps>) {
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
        d="M10.833 5.833l-.93-1.859c-.267-.535-.401-.803-.6-.998a1.667 1.667 0 00-.624-.385C8.415 2.5 8.116 2.5 7.518 2.5H4.333c-.934 0-1.4 0-1.757.182-.314.16-.569.414-.728.728-.182.357-.182.823-.182 1.757v.666m0 0h12.667c1.4 0 2.1 0 2.635.273a2.5 2.5 0 011.092 1.092c.273.535.273 1.235.273 2.635V13.5c0 1.4 0 2.1-.273 2.635a2.5 2.5 0 01-1.092 1.092c-.535.273-1.235.273-2.635.273H5.666c-1.4 0-2.1 0-2.635-.273a2.5 2.5 0 01-1.093-1.092c-.272-.535-.272-1.235-.272-2.635V5.833zm8.333 8.334v-5m-2.5 2.5h5"
        stroke="currentColor"
        strokeWidth={1.66667}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
