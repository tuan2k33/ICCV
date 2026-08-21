import toast from 'react-hot-toast'
import CheckCircleIcon from '~/assets/icons/check-circle.svg'

export const toastSuccess = (message: string) =>
  toast.success(message, {
    icon: (
      <CheckCircleIcon
        className="text-[#079455] rounded-full shrink-0 text-xl"
        style={{
          boxShadow: `0 0 0 2px white, 0 0 0 4px #0794554D, 0 0 0 6px white, 0 0 0 8px #0794551A`,
        }}
      />
    ),
    className:
      '!text-[#079455] text-sm font-semibold gap-3 !pl-4 border border-border-primary !rounded-xl min-h-13 !max-w-[unset]',
  })
