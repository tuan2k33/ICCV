import type { IconProps } from '~/types/common'

export default function ExcelDownloadIcon(props: Readonly<IconProps>) {
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
        d="M16.667 10.417v-4.75c0-1.4 0-2.1-.272-2.635a2.5 2.5 0 00-1.093-1.093c-.534-.272-1.235-.272-2.635-.272H7.334c-1.4 0-2.1 0-2.635.272a2.5 2.5 0 00-1.093 1.093c-.272.534-.272 1.234-.272 2.635v8.666c0 1.4 0 2.1.272 2.635A2.5 2.5 0 004.7 18.061c.535.272 1.235.272 2.635.272h3.083m2.084-2.5l2.5 2.5m0 0l2.5-2.5m-2.5 2.5v-5"
        stroke="currentColor"
        strokeWidth={1.66667}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <rect
        x={6.66602}
        y={5.83337}
        width={6.75758}
        height={7.5}
        rx={2}
        fill="url(#paint0_linear_1255_19882)"
      />
      <path
        d="M11.734 11.667l-1.19-2.125L11.682 7.5h-.929l-.702 1.304L9.36 7.5h-.958l1.144 2.042-1.19 2.125h.928l.75-1.381.742 1.38h.958z"
        fill="#fff"
      />
      <defs>
        <linearGradient
          id="paint0_linear_1255_19882"
          x1={6.66602}
          y1={9.58337}
          x2={13.4236}
          y2={9.58337}
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#185A30" />
          <stop offset={1} stopColor="#176F3D" />
        </linearGradient>
      </defs>
    </svg>
  )
}
