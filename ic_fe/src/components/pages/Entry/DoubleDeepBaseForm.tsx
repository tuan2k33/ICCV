import React, { useEffect, useRef, type ChangeEvent } from 'react'
import type { FormikErrors, useFormik } from 'formik'
import { useSelector } from 'react-redux'
import { twMerge } from 'tailwind-merge'
import type { PalletStatus } from '~/types/task'
import type { RootState } from '~/redux'
import MinusCircle from '~/assets/icons/minus-circle.svg'
import PlusCircleIcon from '~/assets/icons/plus-circle.svg'
import Input from '~/components/common/Input'
import CheckBox from '~/components/common/CheckBox'
import { type FormValues } from '.'

interface Props {
  prefix: string
  form: ReturnType<typeof useFormik<FormValues>>
  label: string
  autoFocus?: boolean
  allowFullCheck?: boolean | 'disable'
  onInputChange: (e: ChangeEvent<HTMLInputElement>) => void
  focusSubmitButton: (delay?: number) => void
}

export default function DoubleDeepBaseForm({
  prefix,
  form,
  label,
  autoFocus,
  allowFullCheck = false,
  onInputChange,
  focusSubmitButton,
}: Readonly<Props>) {
  const missingOnLayerWrapperRef = useRef<HTMLDivElement>(null)
  const { user } = useSelector((state: RootState) => state.auth)
  const editable = user?.company !== 'Linfox'

  useEffect(() => {
    if (!(document.activeElement instanceof HTMLInputElement)) return
    let isCalculateAble = true

    if (
      Object.keys(form.errors).some((key) =>
        key.startsWith(`double_deep.${prefix}missing_on_layer`),
      )
    )
      isCalculateAble = false

    if (isCalculateAble) {
      if (
        form.errors[`double_deep.${prefix}layer_count` as keyof FormikErrors<FormValues>] ||
        form.errors[
          `double_deep.${prefix}top_layer_product_count` as keyof FormikErrors<FormValues>
        ]
      )
        isCalculateAble = false
    }

    if (
      isCalculateAble &&
      (!form.values.double_deep[`${prefix}layer_count` as keyof FormValues['double_deep']] ||
        !form.values.double_deep[
          `${prefix}top_layer_product_count` as keyof FormValues['double_deep']
        ])
    )
      isCalculateAble = false

    if (isCalculateAble) {
      const layer_count = Number(
          form.values.double_deep[`${prefix}layer_count` as keyof FormValues['double_deep']],
        ),
        top_layer_product_count = Number(
          form.values.double_deep[
            `${prefix}top_layer_product_count` as keyof FormValues['double_deep']
          ],
        ),
        missingOnLayer = (
          form.values.double_deep[
            `${prefix}missing_on_layer` as keyof FormValues['double_deep']
          ] as string[]
        ).reduce((prev, currentVal) => prev + Number(currentVal) || 0, 0)

      const total = layer_count * top_layer_product_count + missingOnLayer

      form.setFieldValue(`double_deep.${prefix}total`, total + '')
    } else {
      const activeElement = document.activeElement

      if (
        (!(activeElement instanceof HTMLInputElement) ||
          activeElement.name !== `double_deep.${prefix}total`) &&
        (form.errors[`double_deep.${prefix}layer_count` as keyof FormikErrors<FormValues>] ||
          form.errors[
            `double_deep.${prefix}top_layer_product_count` as keyof FormikErrors<FormValues>
          ])
      ) {
        form.setFieldValue(`double_deep.${prefix}total`, '')
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.values, form.errors])

  const handleInsertNewMissingField = () => {
    form.setFieldValue(
      `double_deep.${prefix}missing_on_layer`,
      [
        ...(form.values.double_deep[
          `${prefix}missing_on_layer` as keyof FormValues['double_deep']
        ] as string[]),
        '',
      ],
      false,
    )
    setTimeout(() => {
      missingOnLayerWrapperRef.current?.scrollTo({
        left: missingOnLayerWrapperRef.current.scrollWidth,
        behavior: 'smooth',
      })
    }, 100)
  }

  const handleChangeStatus = (status: PalletStatus, checked: boolean) => {
    let payload: Record<string, unknown>

    if (!checked)
      payload = {
        [`${prefix}status`]: null,
        [`${prefix}layer_count`]: '',
        [`${prefix}top_layer_product_count`]: '',
        [`${prefix} `]: [''],
        [`${prefix}total`]: '',
      }
    else if (status === 'full') {
      // currently, 'full' only support for inner, so we can hard code here
      payload = {
        [`${prefix}status`]: status,
        [`${prefix}layer_count`]: form.values.double_deep.outer_layer_count,
        [`${prefix}top_layer_product_count`]: form.values.double_deep.outer_top_layer_product_count,
        [`${prefix}missing_on_layer`]: [''],
        [`${prefix}total`]: form.values.double_deep.outer_total,
      }
    } else {
      payload = {
        [`${prefix}status`]: status,
        [`${prefix}layer_count`]: '0',
        [`${prefix}top_layer_product_count`]: '0',
        [`${prefix}missing_on_layer`]: [''],
        [`${prefix}total`]: '0',
      }
    }

    form.setFieldValue('double_deep', { ...form.values.double_deep, ...payload })
    if (checked) focusSubmitButton(100)
  }

  return (
    <div className="flex items-center gap-16">
      <div className="flex items-center justify-between gap-17 min-w-fit shrink-0">
        <p className="font-semibold w-23">{label}</p>
        <div className="flex gap-1 min-w-[262px] justify-between">
          <CheckBox
            label="Trống"
            checked={
              form.values.double_deep[`${prefix}status` as keyof FormValues['double_deep']] ===
              'empty'
            }
            classNames={{
              wrapper: 'flex-col-reverse gap-0',
            }}
            disabled={!editable}
            onChange={(e) => handleChangeStatus('empty', e.target.checked)}
          />
          {allowFullCheck && (
            <CheckBox
              label="Đầy (giống pallet ngoài)"
              checked={
                form.values.double_deep[`${prefix}status` as keyof FormValues['double_deep']] ===
                'full'
              }
              classNames={{
                wrapper: twMerge(
                  'flex-col-reverse gap-0',
                  allowFullCheck === 'disable' && 'opacity-50',
                ),
              }}
              disabled={allowFullCheck === 'disable'}
              onChange={(e) => handleChangeStatus('full', e.target.checked)}
            />
          )}
        </div>
      </div>
      {form.values.double_deep[`${prefix}status` as keyof FormValues['double_deep']] !==
        'empty' && (
        <div className="flex items-center gap-6">
          <Input
            label="SL lớp đầy"
            className="w-20 text-base"
            classnames={{
              label: 'text-sm',
            }}
            placeholder={editable ? 'Nhập' : ''}
            name={`double_deep.${prefix}layer_count`}
            autoFocus={autoFocus}
            value={
              form.values.double_deep[
                `${prefix}layer_count` as keyof FormValues['double_deep']
              ] as string
            }
            touched={
              form.touched.double_deep?.[`${prefix}layer_count` as keyof FormValues['double_deep']]
            }
            errorStatusWithOutMessage={
              !!form.errors[`double_deep.${prefix}layer_count` as keyof FormikErrors<FormValues>]
            }
            readOnly={!editable}
            onChange={onInputChange}
          />
          <Input
            label="SL thùng/lớp đầy"
            className="w-31 text-base"
            classnames={{
              label: 'text-sm',
            }}
            placeholder={editable ? 'Nhập' : ''}
            name={`double_deep.${prefix}top_layer_product_count`}
            value={
              form.values.double_deep[
                `${prefix}top_layer_product_count` as keyof FormValues['double_deep']
              ] as string
            }
            touched={
              form.touched.double_deep?.[
                `${prefix}top_layer_product_count` as keyof FormValues['double_deep']
              ]
            }
            errorStatusWithOutMessage={
              !!form.errors[
                `double_deep.${prefix}top_layer_product_count` as keyof FormikErrors<FormValues>
              ]
            }
            readOnly={!editable}
            onChange={onInputChange}
          />
          <div
            className="overflow-x-auto max-w-76 scrollbar-xs -mt-4 pt-3 pb-1 -mb-2"
            ref={missingOnLayerWrapperRef}
          >
            <div className="flex items-center gap-6 w-fit">
              {(
                form.values.double_deep[
                  `${prefix}missing_on_layer` as keyof FormValues['double_deep']
                ] as string[]
              ).map((val, index) => (
                <Input
                  key={index + ''}
                  name={`double_deep.${prefix}missing_on_layer[${index}]`}
                  label={`SL thùng/lớp lẻ ${
                    (
                      form.values.double_deep[
                        `${prefix}missing_on_layer` as keyof FormValues['double_deep']
                      ] as string[]
                    ).length > 1
                      ? index + 1
                      : ''
                  }`}
                  className="text-base"
                  classnames={{
                    wrapper: 'w-35',
                    label: 'text-sm',
                  }}
                  placeholder={editable ? '0' : ''}
                  touched={
                    form.touched.double_deep?.[
                      `${prefix}missing_on_layer` as keyof FormValues['double_deep']
                    ]
                  }
                  errorStatusWithOutMessage={
                    !!form.errors[
                      `double_deep.${prefix}missing_on_layer[${index}]` as keyof FormikErrors<FormValues>
                    ]
                  }
                  tabIndex={
                    index === 0 &&
                    (
                      form.values.double_deep[
                        `${prefix}missing_on_layer` as keyof FormValues['double_deep']
                      ] as string[]
                    ).length === 1 &&
                    (
                      form.values.double_deep[
                        `${prefix}missing_on_layer` as keyof FormValues['double_deep']
                      ] as string[]
                    )[index] +
                      '' ===
                      '0'
                      ? -1
                      : undefined
                  }
                  value={val}
                  readOnly={!editable}
                  onChange={onInputChange}
                />
              ))}
            </div>
          </div>

          {(
            form.values.double_deep[
              `${prefix}missing_on_layer` as keyof FormValues['double_deep']
            ] as string[]
          ).length > 1 &&
            editable && (
              <button
                className="text-xl -ml-2 cursor-pointer"
                type="button"
                onClick={() => {
                  const newValues = [
                    ...(form.values.double_deep[
                      `${prefix}missing_on_layer` as keyof FormValues['double_deep']
                    ] as string[]),
                  ]
                  newValues.splice(-1)
                  form.setFieldValue(`double_deep.${prefix}missing_on_layer`, newValues, false)
                }}
              >
                <MinusCircle />
              </button>
            )}

          {editable && (
            <button
              className="text-xl -ml-2 cursor-pointer disabled:cursor-not-allowed disabled:opacity-60"
              type="button"
              onClick={handleInsertNewMissingField}
            >
              <PlusCircleIcon />
            </button>
          )}

          <Input
            name={`double_deep.${prefix}total`}
            label="Tổng"
            className="w-14 text-base"
            classnames={{
              label: 'text-sm',
            }}
            value={
              form.values.double_deep[`${prefix}total` as keyof FormValues['double_deep']] as string
            }
            touched={
              form.touched.double_deep?.[`${prefix}total` as keyof FormValues['double_deep']]
            }
            errorStatusWithOutMessage={
              !!form.errors[`double_deep.${prefix}total` as keyof FormikErrors<FormValues>]
            }
            onChange={onInputChange}
          />
        </div>
      )}
    </div>
  )
}
