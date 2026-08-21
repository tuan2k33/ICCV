import type { IconProps } from '~/types/common'

export default function PencilIcon(props: Readonly<IconProps>) {
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
        d="M2.084 17.917l4.624-1.779c.296-.114.444-.17.582-.245.123-.066.24-.142.35-.227.125-.097.237-.209.46-.433l9.4-9.4A2.357 2.357 0 0014.168 2.5l-9.4 9.4c-.224.224-.336.336-.432.46-.085.11-.162.227-.227.35a5.202 5.202 0 00-.245.582l-1.779 4.625zm0 0l1.715-4.46c.123-.319.184-.478.29-.551a.417.417 0 01.315-.067c.126.024.247.145.489.386l1.882 1.883c.242.242.363.363.387.489a.417.417 0 01-.067.315c-.073.105-.233.167-.552.29l-4.459 1.715z"
        stroke="currentColor"
        strokeWidth={1.66667}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
