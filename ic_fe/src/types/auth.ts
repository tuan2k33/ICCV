export enum Role {
  ADMIN = 'ADMIN',
  ENTRY = 'ENTRY',
  CHECKER = 'CHECKER',
}

export interface User {
  id: number
  username: string
  email: string
  fullname: string | null
  phone_number: any
  gender: any
  address: any
  is_active: boolean
  roles: Role[]
  created_at: string
  updated_at: string
  deleted_at: string | null
  company: 'Linfox' | 'Unilever' // TODO
  tenant_id: number
}
