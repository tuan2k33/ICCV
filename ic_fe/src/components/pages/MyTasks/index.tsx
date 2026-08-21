import { useMemo } from 'react'
import { Link } from 'react-router'
import { twMerge } from 'tailwind-merge'
import { useSelector } from 'react-redux'

import { endpoints } from '~/configs/endpoints'
import { useGet } from '~/hooks/useGet'
import { TaskRecordStatus, TaskStatus, type ListTaskItem } from '~/types/task'
import { formatDateTime } from '~/utils/formatDateTime'
import { toastError } from '~/utils/showErrorToast'
import type { RootState } from '~/redux'

import Empty from '~/components/common/Empty'
import Loading from '~/components/common/Loading'
import Progress from '~/components/common/Progress'

export default function MyTasks() {
  const { user } = useSelector((state: RootState) => state.auth)

  const myTasks = useGet<{
    total: number
    tasks: ListTaskItem[]
  }>({
    url: endpoints.MY_TASKS,
    config: {
      params: {
        skip: 0,
        limit: 999,
      },
    },
  })

  const taskStatistic = useMemo(() => {
    let haveInprogressTask = false
    const completedTaskCount = myTasks.response?.tasks.reduce((prevCount, task) => {
      if (!haveInprogressTask && task.status === TaskStatus.IN_PROGRESS) haveInprogressTask = true
      return prevCount + (task.status === TaskStatus.COMPLETED ? 1 : 0)
    }, 0)

    return {
      completedTaskCount,
      haveInprogressTask,
    }
  }, [myTasks.response?.tasks])

  const sortedTask = useMemo(() => {
    const groupTask: {
      inprogress: ListTaskItem[]
      notStarted: ListTaskItem[]
      notAvailable: ListTaskItem[]
      completed: ListTaskItem[]
    } = {
      inprogress: [],
      notStarted: [],
      notAvailable: [],
      completed: [],
    }

    for (const task of myTasks.response?.tasks ?? []) {
      if (task.status === TaskStatus.COMPLETED) {
        groupTask.completed.push(task)
        continue
      }

      if (task.status === TaskStatus.IN_PROGRESS) {
        groupTask.inprogress.push(task)
        continue
      }

      if (task.status === TaskStatus.NOT_STARTED) {
        if (task.record_status === TaskRecordStatus.COMPLETED) groupTask.notStarted.push(task)
        else groupTask.notAvailable.push(task)
      }
    }

    return [
      ...groupTask.inprogress,
      ...groupTask.notStarted,
      ...groupTask.notAvailable,
      ...groupTask.completed,
    ]
  }, [myTasks.response?.tasks])

  const renderStatus = (status: TaskStatus, taskRecordStatus: TaskRecordStatus) => {
    if (status === TaskStatus.IN_PROGRESS)
      return <span className="text-xs font-bold text-blue-secondary">Tiếp tục</span>
    if (taskRecordStatus === TaskRecordStatus.IN_PROGRESS) return null
    if (status === TaskStatus.NOT_STARTED)
      return <span className="text-xs text-text-default-secondary">Chưa đếm</span>

    if (status === TaskStatus.COMPLETED)
      return <span className="text-success text-xs">Hoàn thành</span>
  }

  const renderProgress = (task: ListTaskItem) => {
    if (task.status === TaskStatus.IN_PROGRESS || task.status === TaskStatus.COMPLETED)
      return (
        <Progress
          current={task.progress}
          total={task.total_progress}
          classNames={{
            label: 'text-xs',
            bar: 'w-[unset] grow',
            progressBar: task.status === TaskStatus.COMPLETED ? 'bg-success' : '',
          }}
        />
      )

    if (task.record_status === TaskRecordStatus.IN_PROGRESS)
      return <p className="text-xs text-text-default-secondary">Đang tiến hành quay</p>

    if (task.status === TaskStatus.NOT_STARTED)
      return <p className="text-xs text-blue-secondary">Đã quay xong</p>
  }

  const renderTime = (task: ListTaskItem) => {
    if (!task.start_time_working) return ''
    if (task.status === TaskStatus.IN_PROGRESS && task.start_time_working)
      return formatDateTime(new Date(task.start_time_working + 'Z'), 'HH:mm DD/M/YYYY')
    if (
      (task.status === TaskStatus.REVIEW || task.status === TaskStatus.COMPLETED) &&
      task.time_submit_e
    )
      return `${formatDateTime(new Date(task.start_time_working + 'Z'), 'HH:mm')} -  ${formatDateTime(new Date(task.time_submit_e + 'Z'), 'HH:mm DD/M/YYYY')}`
  }

  if (myTasks.pending) return <Loading className="h-full" />
  if (!myTasks.response?.tasks.length)
    return <Empty className="h-full" label="Hiện chưa có dãy cần kiểm." />

  return (
    <div className="flex flex-col max-h-full">
      <h1 className="text-xl font-semibold flex items-center justify-center gap-4 pt-3.5 pb-1">
        Task của tôi{' '}
        <span className="block text-sm font-medium text-error-secondary rounded-full h-7 px-2 leading-7 border border-[#FF6A60] bg-[#FFB5B0]">
          Hoàn thành {taskStatistic.completedTaskCount}/{myTasks.response.total} dãy
        </span>
      </h1>
      <div className="grid gap-x-5 gap-y-4 flex-wrap p-4 grid-cols-[repeat(auto-fill,minmax(230px,1fr))] grow overflow-y-auto">
        {sortedTask?.map((task) => {
          let disabled = task.record_status === TaskRecordStatus.IN_PROGRESS

          if (
            !disabled &&
            user?.company !== 'Linfox' &&
            task.status !== TaskStatus.IN_PROGRESS &&
            task.status !== TaskStatus.NOT_STARTED
          ) {
            disabled = true
          }

          const [name, type] = task.rack_name.split('-')

          return (
            <Link
              to={`/entry/${task.id}`}
              key={task.id}
              className={twMerge(
                'px-3 py-2.5 rounded-lg shadow-[0_4px_10px_#00000026] border-2 border-transparent hover:border-primary',
                disabled && 'bg-[#F3F3F3] pointer-events-none',
              )}
              onClick={(e) => {
                if (disabled) e.preventDefault()
                else if (
                  user?.company !== 'Linfox' &&
                  taskStatistic.haveInprogressTask &&
                  task.status !== TaskStatus.IN_PROGRESS
                ) {
                  toastError('Hãy tiếp tục kiểm dãy hiện tại.')
                  e.preventDefault()
                }
              }}
            >
              <div className="flex items-center justify-between">
                <p
                  className={twMerge(
                    'text-sm font-semibold',
                    disabled &&
                      task.status !== TaskStatus.COMPLETED &&
                      'text-text-default-secondary',
                  )}
                >
                  Dãy {name} {type === 'even' ? 'chẵn' : 'lẻ'}
                </p>
                {renderStatus(task.status, task.record_status)}
              </div>
              <p className="my-3.5 text-xs min-h-4">{renderTime(task)}</p>
              {renderProgress(task)}
            </Link>
          )
        })}
      </div>
    </div>
  )
}
