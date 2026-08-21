import toast from 'react-hot-toast'
import AlertCircleIcon from '~/assets/icons/alert-circle.svg'
export const toastError = (message: string) =>
  toast.error(message, {
    icon: (
      <AlertCircleIcon
        className="text-error-secondary rounded-full shrink-0 text-xl"
        style={{
          boxShadow: `0 0 0 2px white, 0 0 0 4px #BB1B0F4D, 0 0 0 6px white, 0 0 0 8px #BB1B0F1A`,
        }}
      />
    ),
    className:
      '!text-error-secondary text-sm font-semibold gap-3 !pl-4 border border-border-primary !rounded-xl min-h-13 !max-w-[unset]',
  })
