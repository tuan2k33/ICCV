import type { SVGAttributes } from 'react'
import type { Role } from './auth'

export interface IconProps extends SVGAttributes<SVGElement> {}

export interface CountingPairListItem {
  id: number
  code: string
  batch_id: number
  user_id_1: number | null
  fullname_1: string | null
  user_id_2: number | null
  fullname_2: string | null
  racks?: string[] | null
  process: number
}

export interface CountingPairGridItem {
  code: string
  id: number
  rack_name: string
}

export interface UserCommon {
  id: number
  username: string
  fullname: string
  phone_number: string
  roles: Role[]
  company: string
}
