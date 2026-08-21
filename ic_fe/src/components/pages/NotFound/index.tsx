import { Link } from 'react-router'
import logo from '~/assets/logo.png'

export default function NotFound() {
  return (
    <div className="h-dvh flex items-center justify-center flex-col relative overflow-hidden">
      <p className="absolute text-[200px] sm:text-[300px] font-bold left-1/2 top-1/2 opacity-10 scale-y-150 -translate-x-1/2 -translate-y-1/2 select-none flex items-center">
        40<span className="rotate-y-180 inline-block translate-z-0">4</span>
      </p>
      <p className="text-4xl font-semibold text-text-default-secondary relative z-10">
        PAGE NOT FOUND
      </p>
      <p className="text-sm font-semibold text-text-default-secondary mt-2 text-balance text-center px-1">
        The page you are looking for does not exist. It might have been moved or deleted.
      </p>
      <div className="flex items-center gap-5 mt-8 ">
        <img src={logo} alt="logo" className="object-cover w-[160px]" />
        <Link
          to="/"
          replace
          className="font-semibold text-primary block rounded-lg px-3 py-2 hover:backdrop-blur-xs hover:bg-primary/10 relative z-10 duration-200"
        >
          Go Home
        </Link>
      </div>
    </div>
  )
}
