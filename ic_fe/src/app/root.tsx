import { useEffect } from 'react'
import {
  isRouteErrorResponse,
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  useLocation,
} from 'react-router'
import { Provider, useDispatch, useSelector } from 'react-redux'
import { Toaster } from 'react-hot-toast'

import type { Route } from './+types/root'
import { store, type AppDispatch, type RootState } from '~/redux'
import { actionThunkGetMe } from '~/redux/slices/auth'
import Loading from '~/components/common/Loading'
import NotFound from '~/components/pages/NotFound'
import './app.css'

export const links: Route.LinksFunction = () => [
  {
    rel: 'preload',
    href: '/fonts/PublicSans-VariableFont_wght.ttf',
    as: 'font',
    type: 'font/ttf',
    crossOrigin: 'anonymous',
  },
  {
    rel: 'preload',
    href: '/fonts/PublicSans-Italic-VariableFont_wght.ttf',
    as: 'font',
    type: 'font/ttf',
    crossOrigin: 'anonymous',
  },
]

const pathToTitleMap: Record<string, string> = {
  '/auth/login': 'Login',
  '/': 'Home',
  '/entry': 'Entry',
  '/check': 'Check',
  '/tasks': 'My tasks',
  '/dashboard': 'Dashboard',
}

export function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  const location = useLocation()
  const path = location.pathname

  useEffect(() => {
    if (path === '/entry') {
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'F5' || e.keyCode === 116) {
          e.preventDefault()
        }
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'r') {
          e.preventDefault()
        }
      }

      window.addEventListener('keydown', handleKeyDown)

      return () => window.removeEventListener('keydown', handleKeyDown)
    }
  }, [path])

  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{pathToTitleMap[path]}</title>
        <Meta />
        <Links />
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  )
}

export default function App() {
  return (
    <Provider store={store}>
      <InitRedux>
        <Outlet />
      </InitRedux>
      <Toaster />
    </Provider>
  )
}

function InitRedux({ children }: Readonly<{ children: React.ReactNode }>) {
  const dispatch = useDispatch<AppDispatch>()
  const { loading } = useSelector((state: RootState) => state.auth)

  useEffect(() => {
    dispatch(actionThunkGetMe())
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (loading) {
    return <Loading className="absolute inset-0" />
  }
  return children
}

export function HydrateFallback() {
  return <Loading className="absolute inset-0" />
}

export function ErrorBoundary({ error }: Readonly<Route.ErrorBoundaryProps>) {
  let message = 'Oops!'
  let details = 'An unexpected error occurred.'
  let stack: string | undefined

  if (isRouteErrorResponse(error)) {
    if (error.status === 404) return <NotFound />
    message = error.status === 404 ? '404' : 'Error'
    details =
      error.status === 404 ? 'The requested page could not be found.' : error.statusText || details
  } else if (import.meta.env.DEV && error && error instanceof Error) {
    details = error.message
    stack = error.stack
  }

  return (
    <main className="pt-16 p-4 container mx-auto">
      <h1>{message}</h1>
      <p>{details}</p>
      {stack && (
        <pre className="w-full p-4 overflow-x-auto">
          <code>{stack}</code>
        </pre>
      )}
    </main>
  )
}
