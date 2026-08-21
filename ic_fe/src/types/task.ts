export interface DefaultPalletData {
  code?: [string]
  empty?: number
  front?: [string]
  product_id?: string
  score_empty?: number
  score_pid?: number
  top?: [string]
  video?: [string]
}

export type TaskResult = Record<string, Record<string, Record<string, unknown> & DefaultPalletData>>

export type TaskFlag = Record<
  string,
  Record<
    string,
    {
      confirm_reason: string
      other_reason?: string
    }
  >
>

export type TimeProcessTask = Record<string, Record<string, number>>

export interface Task {
  id: number
  tenant_id: number
  batch_id: number
  rack_name: string
  user_e1: number
  user_e2: number
  user_c: any
  result_e: TaskResult
  flags_e?: TaskFlag
  flags_c?: TaskFlag | null
  time_process_e?: TimeProcessTask
  time_process_c?: TimeProcessTask | null
  result_c: TaskResult | null
  time_submit: string | null
  release: boolean
  created_at: string
  updated_at: string
  start_time_working: string | null
  status: TaskStatus
  total_progress: number
  user_e: number
  user_view_e: number
}

export interface PackData {
  name: string
  pallets: Pallet[]
}

export interface Pallet {
  name: string
  data: Partial<PalletData>
}

export interface PalletData extends DefaultPalletData, Record<string, unknown> {
  _is_finished: boolean
  _time: number
  _need_confirm: boolean
}

export interface ListTaskItem {
  id: number
  batch_id: number
  rack_name: string
  user_e1: number
  user_e2: number
  user_c: null
  created_at: string
  updated_at: string
  status: TaskStatus
  total_progress: number
  progress: number
  start_time_working: string | null
  time_submit_e: string | null
  record_status: TaskRecordStatus
}

export interface MapRow {
  rack_name: string
  status: TaskStatus
  id: number
  /**
   * for `countingPair`
   */
  pairId?: string | number
}

export type MapPack = { even: MapRow | null; odd: MapRow | null }[]

export type MapAreaData = MapPack[]

export type PalletStatus = 'full' | 'empty' | null

export type RackType = 'SINGLE' | 'DOUBLE' | null

export enum TaskStatus {
  NOT_STARTED = 'NOT_STARTED',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED',
  FLAGGED = 'FLAGGED',
  REVIEW = 'REVIEW',
}

export enum TaskRecordStatus {
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED',
}
