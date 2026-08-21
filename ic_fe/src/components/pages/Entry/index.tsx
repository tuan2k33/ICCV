import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type KeyboardEvent,
  type MouseEvent,
} from 'react'
import { useSelector } from 'react-redux'
import toast from 'react-hot-toast'
import { ObjectSchema, ValidationError } from 'yup'
import { useFormik, type FormikErrors } from 'formik'
import { useNavigate, useParams } from 'react-router'
import { twMerge } from 'tailwind-merge'
import type { AxiosError } from 'axios'

import {
  DoubleDeepEntrySchema,
  EntrySchema,
  errorMessage,
  OtherReasonConfirmEntrySchema,
  SingleDeepEntrySchema,
} from '~/configs/schemas'
import { endpoints } from '~/configs/endpoints'
import { API_URL } from '~/configs/constants'
import { formatString } from '~/utils/formatString'
import { sleep } from '~/utils/sleep'
import { serializeYupError, type SerializedYupError } from '~/utils/serializeYupError'
import { toastError } from '~/utils/showErrorToast'
import {
  TaskStatus,
  type PackData,
  type PalletData,
  type PalletStatus,
  type Task,
  type TaskResult,
  type RackType,
  type DefaultPalletData,
} from '~/types/task'
import { useGet } from '~/hooks/useGet'
import { useMutation } from '~/hooks/useMutation'
import { useModal } from '~/hooks/useModal'
import type { RootState } from '~/redux'
import { ErrorMessage } from '~/configs/errorCode'

import ImageIcon from '~/assets/icons/image.svg'
import PlayIcon from '~/assets/icons/play.svg'
import FlagIcon from '~/assets/icons/flag.svg'

import Button from '~/components/common/Button'
import WorkspaceDataViewer from '~/components/common/WorkspaceDataViewer'
import { type SelectRef } from '~/components/common/Select'
import Input from '~/components/common/Input'
import type { CountingRef } from '~/components/common/Counting'
import Loading from '~/components/common/Loading'
import Empty from '~/components/common/Empty'
import Header from './Header'
import RowButtons, { type RowButtonsRef } from './RowButtons'
import PalletButtons from './PalletButtons'
import SingleDeepForm from './SingleDeepForm'
import DoubleDeepForm from './DoubleDeepForm'
import ConfirmForm from './ConfirmForm'

export const confirmOptions = [
  {
    value: 'blur_image/flash',
    label: 'Ảnh mờ/lóe sáng',
  },
  {
    value: 'missing_camera_angle',
    label: 'Góc quay thiếu',
  },
  {
    value: 'too_thick_plastic_bag/obscured',
    label: 'Bao nilong quá dày/bị che khuất',
  },
  {
    value: 'stray_product',
    label: 'Có sản phẩm lạc vào',
  },
  {
    value: 'other',
    label: 'Khác',
  },
] as const

export interface FormValues {
  location: string
  product_id: string
  _origin_product_id: string
  rack_type: RackType
  confirm_reason: null | (typeof confirmOptions)[number]['value']
  other_reason: string
  single_deep: {
    status: PalletStatus
    layer_count: string
    top_layer_product_count: string
    missing_on_layer: string[]
    total: string
  }
  double_deep: {
    inner_status: PalletStatus
    inner_layer_count: string
    inner_top_layer_product_count: string
    inner_missing_on_layer: string[]
    inner_total: string

    outer_status: PalletStatus
    outer_layer_count: string
    outer_top_layer_product_count: string
    outer_missing_on_layer: string[]
    outer_total: string
  }
}

export const fakeFullData = {
  layer: '4',
  layerProduct: '8',
  total: '32',
}

const initFormikValues: FormValues = {
  location: '',
  product_id: '',
  _origin_product_id: '',
  rack_type: null,
  confirm_reason: null,
  other_reason: '',
  single_deep: {
    status: null,
    layer_count: '',
    top_layer_product_count: '',
    missing_on_layer: [''],
    total: '',
  },

  double_deep: {
    inner_status: null,
    inner_layer_count: '',
    inner_top_layer_product_count: '',
    inner_missing_on_layer: [''],
    inner_total: '',

    outer_status: null,
    outer_layer_count: '',
    outer_top_layer_product_count: '',
    outer_missing_on_layer: [''],
    outer_total: '',
  },
}

const DEFAULT_PALLET_FIELDS = new Set<keyof DefaultPalletData | '_origin_product_id'>([
  'code',
  'empty',
  'front',
  'product_id',
  'score_empty',
  'score_pid',
  'top',
  'video',
  /**
   * we see this key as origin product_id from AI
   */
  '_origin_product_id',
])

export default function Entry({
  roleRequest = 'ENTRY',
}: Readonly<{ roleRequest?: 'ENTRY' | 'CHECKER' }>) {
  const { taskId } = useParams()
  const navigate = useNavigate()
  const { user } = useSelector((state: RootState) => state.auth)

  const [mode, setMode] = useState<'image' | 'video'>('image')
  const [formMode, setFormMode] = useState<'worker' | 'need_confirm'>('worker')
  const [dataPack, setDataPack] = useState<PackData[] | null>(null)
  const [dataPosition, setDataPosition] = useState({
    column: 0,
    pallet: 0,
  })
  const viewCodeModal = useModal()

  const highestPositionRef = useRef({ ...dataPosition })
  const formRef = useRef<HTMLDivElement>(null)
  const prevToastErrorRef = useRef<string>(null)
  const countingRef = useRef<CountingRef>(null)
  const dataPackRef = useRef<PackData[] | null>(null)
  const selectConfirmReasonRef = useRef<SelectRef>(null)
  const formActionRef = useRef({
    isEnter: false,
    isJustFocusFromInput: false,
    isSubmitClick: false,
    isDisableTotal: false,
  })
  const taskNameRef = useRef('')
  const partialUpdatingRef = useRef(false)
  const taskProgressRef = useRef({
    totalTask: 0,
    finishedTaskCount: 0,
  })
  const rowButtonsRef = useRef<RowButtonsRef>(null)

  const rowData = useMemo(() => {
    return dataPack?.map((item) => item.name)
  }, [dataPack])

  const allowFinishRow = useMemo(() => {
    if (!dataPack) return false

    return dataPack.every(({ pallets }) => {
      return pallets.every(({ data }) => data._is_finished)
    })
  }, [dataPack])

  useEffect(() => {
    dataPackRef.current = dataPack
    let finishedTaskCount = 0
    const totalTask = dataPack?.reduce((prevVal, currentItem) => {
      finishedTaskCount += currentItem.pallets.reduce((prevCount, pallet) => {
        if (pallet.data._is_finished || pallet.data._need_confirm) return prevCount + 1
        return prevCount
      }, 0)
      return currentItem.pallets.length + prevVal
    }, 0)

    taskProgressRef.current = {
      totalTask: totalTask ?? 0,
      finishedTaskCount,
    }
  }, [dataPack])

  useEffect(() => {
    restoreFormData()

    if (dataPosition.column > highestPositionRef.current.column) {
      highestPositionRef.current = { ...dataPosition }
    } else if (
      dataPosition.column === highestPositionRef.current.column &&
      dataPosition.pallet > highestPositionRef.current.pallet
    ) {
      highestPositionRef.current.pallet = dataPosition.pallet
    }

    formRef.current?.querySelector<HTMLInputElement>('input[name*="layer_count"]')?.focus()
    setMode('image')

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataPosition])

  useEffect(() => {
    form.validateForm()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formMode])

  const startTaskMutation = useMutation({
    method: 'put',
    url: formatString(endpoints.TASK_START_WORKING, {
      task_id: taskId as string,
    }),
  })

  const taskData = useGet<Task>(
    {
      url: formatString(endpoints.GET_TASK_BY_ID, {
        id: taskId as string,
      }),
    },
    {
      onSuccess(response) {
        if (!isAllowAccessTask(response)) {
          navigate('/', {
            replace: true,
          })
          return
        }

        const responseResult = response.result_c || response.result_e
        const responseTimeProcess =
          roleRequest === 'CHECKER' ? response.time_process_c : response.time_process_e
        const responseFlag = response.flags_c || response.flags_e

        if (!responseResult) return

        const result: PackData[] = []
        const entriesData = Object.entries(responseResult).sort((itemA, itemB) => {
          return itemA[0].localeCompare(itemB[0])
        })

        entriesData.forEach((column, columnIndex) => {
          const palletsEntries = Object.entries(column[1]).sort((palletA, palletB) =>
            palletA[0].localeCompare(palletB[0]),
          )
          result.push({
            name: column[0],
            pallets: palletsEntries.map(([palletName, palletData], palletIndex) => {
              if (responseTimeProcess?.[column[0]][palletName])
                palletData._time = responseTimeProcess?.[column[0]][palletName]

              if (responseFlag?.[column[0]]?.[palletName]) {
                palletData.confirm_reason = responseFlag[column[0]]?.[palletName].confirm_reason
                palletData.other_reason = responseFlag[column[0]]?.[palletName].other_reason
                palletData._need_confirm = true
              } else if (isPalletHasData(palletData)) {
                palletData._is_finished = true
              }

              // update highest position
              if (palletData._is_finished || palletData._need_confirm) {
                // check if last pallet of rack
                if (!palletsEntries[palletIndex + 1]) {
                  if (entriesData[columnIndex + 1]) {
                    highestPositionRef.current.column = columnIndex + 1
                    highestPositionRef.current.pallet = 0
                  } else {
                    highestPositionRef.current.column = columnIndex
                    highestPositionRef.current.pallet = palletIndex
                  }
                } else {
                  highestPositionRef.current.column = columnIndex
                  highestPositionRef.current.pallet = palletIndex + 1
                }
              }

              palletData._origin_product_id = palletData.product_id

              return {
                name: palletName,
                data: palletData,
              }
            }),
          })
        })

        setDataPack(result)
        form.setFieldValue(
          'location',
          result[dataPosition.column].pallets[dataPosition.pallet].name
            .split('-')
            .slice(1)
            .join('-'),
          false,
        )
        if (response.status === TaskStatus.IN_PROGRESS)
          setDataPosition({
            ...highestPositionRef.current,
          })

        setTimeout(() => {
          restoreFormData()
        }, 100)

        if (response.status === TaskStatus.NOT_STARTED && user?.company === 'Unilever')
          startTaskMutation.mutate({})
      },
    },
  )

  const racksInfoTask = useGet<{
    data: Record<string, Record<string, RackType>>
  }>(
    {
      url: formatString(endpoints.TENANT_INFORMATION_RACKS, {
        tenant_id: user?.tenant_id ?? '',
      }),
      config: {
        params: {
          rack: taskData.response?.rack_name,
        },
      },
    },
    {
      disabled: !taskData.response?.rack_name || !dataPack,
      onSuccess() {
        setTimeout(() => {
          restoreFormData()
        }, 100)
      },
    },
  )

  const finishTaskMutation = useMutation({
    url: formatString(endpoints.SUBMIT_TASK, {
      task_id: taskData.response?.id ?? '',
    }),
    method: 'put',
  })

  const flagTaskMutation = useMutation({
    url: formatString(endpoints.TASK_FLAG, { id: taskData.response?.id ?? '' }),
    method: 'put',
  })

  const timeProcessTaskMutation = useMutation({
    url: formatString(endpoints.TASK_TIME_PROCESS_TASK, { id: taskData.response?.id ?? '' }),
    method: 'put',
  })

  const form = useFormik<FormValues>({
    initialValues: {
      ...initFormikValues,
    },
    async onSubmit(values) {
      let newData: Partial<PalletData> & Partial<FormValues> = {
        ...dataPack?.[dataPosition.column].pallets[dataPosition.pallet].data,
        ...values,
      }

      if (formMode === 'need_confirm') {
        newData._need_confirm = true
        newData.confirm_reason = values.confirm_reason

        if (values.confirm_reason === 'other') {
          newData.other_reason = values.other_reason
        }

        delete newData._is_finished
        delete newData.single_deep
        delete newData.double_deep
      } else {
        delete newData._need_confirm
        delete newData.confirm_reason
        delete newData.other_reason
        newData._is_finished = true

        if (newData.rack_type === 'SINGLE') delete newData.double_deep
        else delete newData.single_deep
      }

      newData._time = countingRef.current?.getValue()

      const newDataPack = [...dataPack!]
      newDataPack[dataPosition.column].pallets[dataPosition.pallet].data = newData
      setDataPack(newDataPack)

      moveToNextTask()
      handlePartialUpdate()
    },
    async validate(values) {
      if (formMode === 'need_confirm') return validateNeedConfirmForm(values)

      return validateWorkForm(values)
    },
  })

  useEffect(() => {
    const abortController = new AbortController()

    // handle focus prev input on press arrowLeft keyboard
    const handleKeyDown = (e: globalThis.KeyboardEvent) => {
      if (
        !formRef.current?.contains(document.activeElement) ||
        !(document.activeElement instanceof HTMLInputElement) ||
        document.activeElement.type !== 'text' ||
        form.errors[document.activeElement.name as keyof typeof form.errors]
      )
        return

      const arrowLeft = e.key === 'ArrowLeft' || e.code === 'ArrowLeft' || e.keyCode === 37
      const notShortcutKey = !e.altKey && !e.ctrlKey && !e.metaKey && !e.shiftKey

      if (
        !arrowLeft ||
        !notShortcutKey ||
        document.activeElement.selectionStart !== 0 ||
        document.activeElement.selectionEnd !== 0
      )
        return

      const inputs = Array.from(
        formRef.current?.querySelectorAll<HTMLInputElement>('input:not(:disabled)') ?? [],
      ).filter((input) => input.name !== 'product_id')

      const length = inputs.length

      let isFoundCurrentInput = false

      for (let i = length - 1; i >= 0; i--) {
        if (isFoundCurrentInput) {
          if (inputs[i].tabIndex >= 0) {
            inputs[i].focus()
            break
          }
        }

        if (inputs[i] === document.activeElement) isFoundCurrentInput = true
      }
    }

    formRef.current?.addEventListener('keydown', handleKeyDown, {
      signal: abortController.signal,
    })

    return () => {
      abortController.abort()
    }
  }, [dataPosition, formMode, dataPack, form])

  const isAllowAccessTask = (task: Task) => {
    if (
      task.status === TaskStatus.NOT_STARTED &&
      !Object.keys(task.result_c ?? {}).length &&
      !Object.keys(task.result_e).length
    ) {
      return false
    }

    if (user?.company === 'Unilever') {
      return task.status !== TaskStatus.COMPLETED && task.user_e === user.id
    } else if (user?.company === 'Linfox') return task.user_view_e === user.id

    return true
  }

  /**
   * check is pallet has data out of default data
   */
  const isPalletHasData = (palletData: Record<string, unknown> & DefaultPalletData) => {
    return Object.keys(palletData).some(
      (key) => !DEFAULT_PALLET_FIELDS.has(key as keyof DefaultPalletData),
    )
  }

  const validateNeedConfirmForm = async (values: FormValues): Promise<FormikErrors<FormValues>> => {
    if (!values.confirm_reason) {
      if (form.touched.confirm_reason) {
        showErrorToast(errorMessage.notInputYet)
        selectConfirmReasonRef.current?.open()
      }

      return {
        confirm_reason: errorMessage.notInputYet,
      }
    }

    let serializedError: Record<string, string[]> = {}
    try {
      if (values.confirm_reason === 'other') {
        await OtherReasonConfirmEntrySchema.validate(values, {
          abortEarly: false,
        })
      }

      await EntrySchema.pick(['product_id']).validate(values, {
        abortEarly: false,
      })
    } catch (error) {
      serializedError = serializeYupError(error as ValidationError)
    }
    handleOnValidate(serializedError)

    return serializedError
  }

  const validateWorkForm = async (values: FormValues) => {
    let serializedError: Record<string, string[]> = {}
    try {
      const omitKey = values.rack_type === 'SINGLE' ? 'double_deep' : 'single_deep'
      const validatorSchema = EntrySchema.omit([omitKey])
      await validatorSchema.validate(values, {
        abortEarly: false,
      })
    } catch (error) {
      serializedError = serializeYupError(error as ValidationError)
    }

    handleOnValidate(serializedError)

    return serializedError
  }

  const restoreFormData = async () => {
    const existedData = dataPackRef.current?.[dataPosition.column].pallets[dataPosition.pallet].data
    countingRef.current?.reset((existedData?._time as number) ?? 0)

    setFormTouched(false)

    let rackType: RackType = 'SINGLE'
    if (existedData?.rack_type) {
      rackType = existedData.rack_type as RackType
    } else {
      const rackInfoType =
        racksInfoTask.response?.data?.[dataPackRef.current?.[dataPosition.column]?.name ?? '']?.[
          dataPackRef.current?.[dataPosition.column]?.pallets?.[dataPosition.pallet]?.name ?? ''
        ]

      rackType = rackInfoType ?? rackType
    }

    form.setValues({
      location:
        (existedData?.location as string) ??
        dataPackRef.current?.[dataPosition.column].pallets[dataPosition.pallet].name
          .split('-')
          .slice(1)
          .join('-') ??
        '',
      product_id: (existedData?.product_id as string) ?? '',
      _origin_product_id:
        ((existedData?._origin_product_id as string) || (existedData?.product_id as string)) ?? '',
      rack_type: rackType,
      confirm_reason: (existedData?.confirm_reason as FormValues['confirm_reason']) ?? null,
      other_reason: (existedData?.other_reason as string) ?? '',
      single_deep: (existedData?.single_deep as any) ?? { ...initFormikValues.single_deep },
      double_deep: (existedData?.double_deep as any) ?? { ...initFormikValues.double_deep },
    })

    if (existedData?._need_confirm) setFormMode('need_confirm')
    else setFormMode('worker')
  }

  const setFormTouched = (touched: boolean) => {
    form.setTouched({
      location: touched,
      product_id: touched,
      rack_type: touched,
      confirm_reason: touched,
      other_reason: touched,

      single_deep: {
        layer_count: touched,
        missing_on_layer: touched,
        top_layer_product_count: touched,
        total: touched,
      },

      double_deep: {
        inner_layer_count: touched,
        inner_missing_on_layer: touched,
        inner_top_layer_product_count: touched,
        inner_total: touched,

        outer_layer_count: touched,
        outer_missing_on_layer: touched,
        outer_top_layer_product_count: touched,
        outer_total: touched,
      },
    })
  }

  const moveToNextTask = async () => {
    if (!dataPack) return
    const currentColumn = dataPack[dataPosition.column].pallets

    if (currentColumn[dataPosition.pallet + 1]) {
      setDataPosition((prev) => ({
        ...prev,
        pallet: prev.pallet + 1,
      }))
      setFormMode('worker')
    } else if (dataPack[dataPosition.column + 1]) {
      setDataPosition((prev) => ({
        pallet: 0,
        column: prev.column + 1,
      }))
      setFormMode('worker')
    } else {
      rowButtonsRef.current?.openConfirmModal()
    }

    setFormTouched(false)
  }

  const handleOnValidate = (serializedError: SerializedYupError) => {
    const serializedErrorEntries = Object.entries(serializedError)

    const activeElement = document.activeElement

    if (!formRef.current?.contains(activeElement)) {
      formActionRef.current.isEnter = false
      return
    }

    if (activeElement instanceof HTMLInputElement) {
      const name = activeElement.name

      if (formActionRef.current.isEnter) {
        if (name in serializedError) showErrorToast(serializedError[name][0])
        else handleMoveToNextInput(serializedError)
      }
    } else if (activeElement instanceof HTMLLabelElement && formMode === 'need_confirm') {
      if (formActionRef.current.isEnter) handleMoveToNextInput({})
    } else if (activeElement instanceof HTMLButtonElement && formActionRef.current.isSubmitClick) {
      if (serializedErrorEntries.length) {
        focusToFirstErrorInput(serializedErrorEntries[0][0])
        showErrorToast(serializedErrorEntries[0][1][0])
      }
    }

    formActionRef.current.isEnter = false
    formActionRef.current.isSubmitClick = false
  }

  const handleMoveToNextInput = async (serializedError: SerializedYupError) => {
    const serializedErrorEntries = Object.entries(serializedError)
    if (serializedErrorEntries.length) {
      // focus to error input
      focusToFirstErrorInput(serializedErrorEntries[0][0])
      return
    }

    formActionRef.current.isJustFocusFromInput = true
    focusSubmitButton()
  }

  const focusToFirstErrorInput = (name: string) => {
    ;(formRef.current?.querySelector(`input[name="${name}"]`) as HTMLInputElement)?.focus()
  }

  const focusSubmitButton = async (delay?: number) => {
    if (delay) {
      // wait for other event
      await sleep(delay)
    }

    ;(formRef.current?.querySelector('button[type="submit"]') as HTMLButtonElement | null)?.focus()
  }

  const showErrorToast = (message: string) => {
    toast.dismiss(prevToastErrorRef.current ?? '')
    prevToastErrorRef.current = toastError(message)
  }

  const addPalletReport = ({
    palletData,
    reportData,
    evenOddTypeNumber,
    palletName,
    rowName,
  }: {
    reportData: Record<string, unknown>[]
    palletData: Partial<PalletData> & Partial<FormValues>
    rowName: string
    evenOddTypeNumber: number
    palletName: string
  }) => {
    let count: number | null = null
    if (palletData._is_finished) {
      count =
        palletData.rack_type === 'SINGLE'
          ? Number(palletData.single_deep?.total ?? 0)
          : Number(palletData.double_deep?.inner_total ?? 0) +
            Number(palletData.double_deep?.outer_total ?? 0)
    }
    reportData.push({
      day: rowName,
      'Even/odd': evenOddTypeNumber,
      Level: null,
      'Count sheet': null,
      'Material Description': null,
      'Pallet No': null,
      'Bin name': palletName,
      Material: null,
      Count: count,
    })
  }

  const serializePackDataForSubmitting = () => {
    const submitData: TaskResult = {}
    const reportData: Record<string, unknown>[] = []
    const needConfirmPallets: Record<string, Record<string, Record<string, any>>> = {}
    const timePallets: Record<string, Record<string, number>> = {}
    const _dataPack = structuredClone(dataPack)
    const [rowName, rowNumber] = _dataPack![0].name.split('-')
    const evenOddTypeNumber = Number(rowNumber) % 2

    _dataPack?.forEach((column) => {
      const columnData: TaskResult[string] = {}
      timePallets[column.name] = {}

      column.pallets.forEach((pallet) => {
        const palletData = pallet.data as Partial<PalletData> & Partial<FormValues>
        columnData[pallet.name] = palletData
        timePallets[column.name][pallet.name] = palletData._time ?? 0

        addPalletReport({
          evenOddTypeNumber,
          rowName,
          reportData,
          palletData,
          palletName: pallet.name,
        })

        if (palletData._need_confirm) {
          if (!needConfirmPallets[column.name]) needConfirmPallets[column.name] = {}

          needConfirmPallets[column.name][pallet.name] = {
            confirm_reason: palletData.confirm_reason,
          }

          if (palletData.other_reason)
            needConfirmPallets[column.name][pallet.name].other_reason = palletData.other_reason

          delete columnData[pallet.name]._need_confirm
          delete columnData[pallet.name].confirm_reason
          delete columnData[pallet.name].other_reason
        } else {
          delete columnData[pallet.name]._is_finished
        }
        delete columnData[pallet.name]._time
      })
      submitData[column.name] = columnData
    })

    return { submitData, timePallets, needConfirmPallets, reportData }
  }

  const handleFinish = async (partialUpdate = false) => {
    const serializedData = serializePackDataForSubmitting()

    const [{ error: finishError }, { error: flagError }, { error: timeError }] = await Promise.all([
      finishTaskMutation.mutate(
        {
          body: {
            result: serializedData.submitData,
            progress: taskProgressRef.current.finishedTaskCount,
            report_task: serializedData.reportData,
          },
          config: {
            params: {
              role_request: roleRequest,
              task_release: roleRequest === 'CHECKER' || !partialUpdate,
            },
          },
        },
        {
          onError: (error) => {
            if ((error as AxiosError).status === 403) {
              navigate('/', {
                replace: true,
              })
            }
            if (roleRequest === 'CHECKER') return toast.error(ErrorMessage.UNKNOWN_ERROR)
            if (partialUpdate) return
            toast.error(ErrorMessage.CANNOT_COMPLETE_ERROR)
          },
          onSuccess() {
            if (partialUpdate) return
            toast.success('Thành công')
          },
        },
      ),
      flagTaskMutation.mutate(
        {
          body: serializedData.needConfirmPallets,
          config: {
            params: {
              role_request: roleRequest,
            },
          },
        },
        {
          onError: (error) => {
            if ((error as AxiosError).status === 403) {
              navigate('/', {
                replace: true,
              })
            }
            if (roleRequest === 'CHECKER') return toast.error(ErrorMessage.UNKNOWN_ERROR)
            if (partialUpdate) return
            toast.error(ErrorMessage.SEND_FLAG_ERROR)
          },
        },
      ),
      timeProcessTaskMutation.mutate(
        {
          body: { time_process: serializedData.timePallets },
          config: {
            params: {
              role_request: roleRequest,
            },
          },
        },
        {
          onError: (error) => {
            if ((error as AxiosError).status === 403) {
              navigate('/', {
                replace: true,
              })
            }
            if (roleRequest === 'CHECKER') return toast.error(ErrorMessage.UNKNOWN_ERROR)
            if (partialUpdate) return
            toast.error(ErrorMessage.SEND_TIME_ERROR)
          },
        },
      ),
    ])

    if (!partialUpdate && !finishError && !flagError && !timeError) navigate('/tasks')
  }

  const handlePartialUpdate = async () => {
    partialUpdatingRef.current = true
    await sleep(100)
    await handleFinish(true)
    partialUpdatingRef.current = false
  }

  const handleKeyDownForm = (e: KeyboardEvent) => {
    if (e.code === 'Enter') {
      formActionRef.current.isEnter = true

      if (
        document.activeElement?.tagName !== 'INPUT' &&
        document.activeElement?.tagName !== 'LABEL'
      )
        return

      if (
        !form.touched[
          (document.activeElement as HTMLInputElement).name as keyof typeof form.touched
        ]
      )
        setFormTouched(true)

      form.validateForm(form.values)
    }
  }

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { value } = e.target
    let name = e.target.name

    let fieldValidator: ObjectSchema<any> = EntrySchema.pick([
      name as keyof typeof EntrySchema.fields,
    ])

    if (name.startsWith('single_deep')) {
      name = name.replace('single_deep.', '')
      fieldValidator = SingleDeepEntrySchema.pick([
        name as keyof typeof SingleDeepEntrySchema.fields,
      ])
    } else if (name.startsWith('double_deep')) {
      name = name.replace('double_deep.', '')
      fieldValidator = DoubleDeepEntrySchema.pick([
        name as keyof typeof DoubleDeepEntrySchema.fields,
      ])
    }

    try {
      fieldValidator.validateSync({
        [name]: value,
      })
    } catch (error) {
      const er = error as ValidationError
      showErrorToast(er.message)
      form.setFieldError(e.target.name, er.message)
      form.setFieldTouched(e.target.name, true, false)

      if (value !== '') return
    }

    if (e.target.name.startsWith('double_deep')) return handleInputDoubleDeepChange(e)

    const parseValue = Number(value)
    const newSetValue = parseValue ? parseValue + '' : value
    if (e.target.name === 'single_deep.total') {
      form.setValues({
        ...form.values,
        single_deep: {
          total: newSetValue,
          layer_count: '',
          missing_on_layer: [''],
          top_layer_product_count: '',
          status: null,
        },
      })
    } else {
      form.setFieldValue(e.target.name, newSetValue)
    }
  }

  const handleInputDoubleDeepChange = (e: ChangeEvent<HTMLInputElement>) => {
    const prefix = e.target.name.includes('inner_') ? 'inner_' : 'outer_'
    const value = e.target.value
    const parseValue = Number(value)
    const newSetValue = parseValue ? parseValue + '' : value
    if (e.target.name.includes('total')) {
      form.setValues({
        ...form.values,
        double_deep: {
          ...form.values.double_deep,
          [`${prefix}layer_count`]: '',
          [`${prefix}missing_on_layer`]: [''],
          [`${prefix}top_layer_product_count`]: '',
          [`${prefix}total`]: newSetValue,
        },
      })
    } else {
      form.setFieldValue(e.target.name, newSetValue)
    }
  }

  const handleChangePosition = (index: number, type: 'column' | 'pallet') => {
    if (type === 'pallet') {
      if (
        dataPosition.column === highestPositionRef.current.column &&
        index > highestPositionRef.current.pallet
      ) {
        return
      }
      setDataPosition((prev) => ({
        ...prev,
        pallet: index,
      }))
    } else {
      if (index > highestPositionRef.current.column) return
      setDataPosition({
        pallet: 0,
        column: index,
      })
    }
  }

  const handleChangeFormMode = (e: MouseEvent<HTMLButtonElement>) => {
    e.currentTarget.blur()
    if (formMode === 'worker') form.setFieldValue('confirm_reason', confirmOptions[0].value, false)
    else {
      form.setValues({ ...form.values, confirm_reason: null, other_reason: '' }, false)
    }
    setFormMode(formMode === 'worker' ? 'need_confirm' : 'worker')
  }

  const handleProductCodeChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (!e.target.value) {
      form.setFieldValue(e.target.name, e.target.value)
      form.setFieldTouched(e.target.name, true, false)
      return
    }
    if (!/^\d+$/.test(e.target.value)) {
      showErrorToast(errorMessage.onlyNumber)
      form.setFieldTouched(e.target.name, true, false)

      return
    }

    if (e.target.value.length <= 8) form.setFieldValue(e.target.name, e.target.value)
  }

  const handleSubmitClick = () => {
    formActionRef.current.isSubmitClick = true
    if (!formActionRef.current.isJustFocusFromInput) form.submitForm()
    formActionRef.current.isJustFocusFromInput = false
  }

  const submitButton =
    user?.company === 'Linfox' ? (
      <></>
    ) : (
      <Button
        className="w-fit h-10 bg-success font-bold text-base px-4 outline-0 focus:ring-4 ring-[#F2B32C66] ml-2"
        type="submit"
        onClick={handleSubmitClick}
        disabled={!!Object.keys(form.errors).length}
      >
        XONG
      </Button>
    )

  const getTaskName = () => {
    if (!taskData.response?.rack_name) return ''
    if (!taskNameRef.current) {
      const taskName = taskData.response.rack_name.split('-')
      taskNameRef.current = `${taskName[0]} ${taskName[1] === 'even' ? 'chẵn' : 'lẻ'}`
    }
    return taskNameRef.current
  }

  if (!dataPack)
    return (
      <div className="h-dvh max-h-dvh flex flex-col">
        <Header isEmpty={true} />
        {taskData.pending ? <Loading className="grow" /> : <Empty className="grow" />}
      </div>
    )

  const renderForm = () => {
    return form.values.rack_type === 'SINGLE' ? (
      <SingleDeepForm
        form={form}
        submitButton={submitButton}
        onInputChange={handleInputChange}
        focusSubmitButton={focusSubmitButton}
      />
    ) : (
      <DoubleDeepForm
        form={form}
        submitButton={submitButton}
        onInputChange={handleInputChange}
        showErrorToast={showErrorToast}
        focusSubmitButton={focusSubmitButton}
      />
    )
  }

  const getRackTypeDisplayValue = (rackType: RackType) => {
    if (!rackType) return ''
    return rackType === 'SINGLE' ? 'Single deep' : 'Double deep'
  }

  const getImages = () => {
    const images: {
      top?: string
      front?: string
      code?: string
    } = {}

    const topUtl = dataPack?.[dataPosition.column].pallets[dataPosition.pallet].data.top?.[0]
    const frontUrl = dataPack?.[dataPosition.column].pallets[dataPosition.pallet].data.front?.[0]
    const codeUrl = dataPack?.[dataPosition.column].pallets[dataPosition.pallet].data.code?.[0]
    if (topUtl) images.top = `${API_URL}/api/blob/${topUtl}`
    if (frontUrl) images.front = `${API_URL}/api/blob/${frontUrl}`
    if (codeUrl) images.code = `${API_URL}/api/blob/${codeUrl}`

    return images
  }

  return (
    <div className="h-dvh max-h-dvh flex flex-col">
      <Header
        current={taskProgressRef.current.finishedTaskCount}
        total={taskProgressRef.current.totalTask}
        countingRef={countingRef}
        taskName={getTaskName()}
      />
      <div className="grow flex flex-col p-3 gap-3">
        <div className="grow basis-0 flex items-stretch">
          <div className="grow flex flex-col gap-3.5">
            <div className="shrink-0 pl-[46px]">
              <div ref={formRef} onKeyDown={handleKeyDownForm}>
                <div className="flex items-center gap-5 pt-2 justify-between">
                  <div className="flex items-center gap-16">
                    <div className="flex items-center gap-4">
                      <Button className="h-9 px-3 text-lg" onClick={viewCodeModal.openModal}>
                        Vị trí:
                      </Button>
                      <p className="text-base shrink-0">
                        {taskData.response?.rack_name.slice(0, 3)}
                        {form.values.location}
                      </p>
                    </div>

                    <p className="text-base flex items-center gap-4">
                      <span className="text-lg font-semibold">Loại rack:</span>{' '}
                      {getRackTypeDisplayValue(form.values.rack_type)}
                    </p>

                    <div className="flex items-center gap-4">
                      <p className="text-lg font-semibold">Mã hàng:</p>
                      <Input
                        className="w-[110px] text-base"
                        classnames={{
                          wrapper: 'h-9',
                        }}
                        placeholder={user?.company === 'Linfox' ? '' : 'Nhập'}
                        name="product_id"
                        value={form.values.product_id}
                        touched={form.touched.product_id}
                        errorStatusWithOutMessage={!!form.errors.product_id}
                        onChange={handleProductCodeChange}
                        disabled={user?.company === 'Linfox'}
                      />
                    </div>
                  </div>

                  <div className="flex items-center gap-8">
                    <button
                      className="ml-auto text-blue-secondary text-sm font-semibold cursor-pointer disabled:cursor-not-allowed disabled:opacity-50 shrink-0 whitespace-nowrap p-1 flex items-center"
                      disabled={
                        !dataPack?.[dataPosition.column].pallets[dataPosition.pallet].data
                          .video?.[0]
                      }
                      type="button"
                      onClick={() => setMode(mode === 'image' ? 'video' : 'image')}
                    >
                      {mode === 'image' ? (
                        <>
                          Xem video
                          <PlayIcon className="ml-1 text-xl" />
                        </>
                      ) : (
                        <>
                          Xem ảnh
                          <ImageIcon className="ml-1 text-xl" />
                        </>
                      )}
                    </button>
                    {user?.company !== 'Linfox' && (
                      <Button
                        className={twMerge(
                          'ml-auto w-fit text-error h-9 border-[#FF4438] shrink-0 text-sm',
                          formMode === 'need_confirm' && 'border-transparent shadow-none',
                        )}
                        outline
                        type="button"
                        tabIndex={-1}
                        onClick={handleChangeFormMode}
                      >
                        {formMode === 'need_confirm'
                          ? 'Đã yêu cầu xác minh lại'
                          : 'Yêu cầu xác minh lại'}{' '}
                        <FlagIcon
                          fill={formMode === 'need_confirm' ? 'currentColor' : 'none'}
                          className="ml-1"
                        />
                      </Button>
                    )}
                  </div>
                </div>
                <div className="pt-6">
                  {formMode === 'worker' ? (
                    renderForm()
                  ) : (
                    <ConfirmForm form={form} formRef={formRef} submitButton={submitButton} />
                  )}
                </div>
              </div>
            </div>
            <div className="grow flex gap-3">
              <PalletButtons
                currentPosition={dataPosition.pallet}
                pallets={dataPack?.[dataPosition.column].pallets ?? []}
                onChange={(index) => {
                  handleChangePosition(index, 'pallet')
                }}
              />
              <WorkspaceDataViewer
                key={dataPack[dataPosition.column].pallets[dataPosition.pallet].name}
                type={mode}
                images={getImages()}
                videoUrl={
                  dataPack?.[dataPosition.column].pallets[dataPosition.pallet].data.video?.[0]
                    ? `${API_URL}/api/blob/${dataPack?.[dataPosition.column].pallets[dataPosition.pallet].data.video?.[0]}`
                    : undefined
                }
                viewCodeModal={viewCodeModal}
              />
            </div>
          </div>
        </div>

        <RowButtons
          list={rowData ?? []}
          currentPosition={dataPosition.column}
          allowFinish={allowFinishRow}
          dataPack={dataPack}
          ref={rowButtonsRef}
          taskName={getTaskName()}
          onFinish={handleFinish}
          onChange={(index) => {
            handleChangePosition(index, 'column')
          }}
        />
      </div>

      {(finishTaskMutation.pending ||
        timeProcessTaskMutation.pending ||
        flagTaskMutation.pending) &&
        !partialUpdatingRef.current && (
          <Loading
            className="fixed inset-0 z-10"
            label={<p className="text-lg font-bold mt-4">Submitting task</p>}
          />
        )}
    </div>
  )
}
