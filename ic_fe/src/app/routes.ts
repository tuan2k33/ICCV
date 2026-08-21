import { type RouteConfig, index, layout, route } from '@react-router/dev/routes'

export default [
  layout('../components/layout/ProtectedLayout.tsx', [
    index('routes/home.tsx'),
    route('tasks', 'routes/tasks.tsx'),
    route('dashboard', 'routes/dashboard.tsx'),
    route('admin', 'routes/admin.tsx'),
  ]),
  layout('../components/layout/HeadlessProtectedLayout.tsx', [
    route('entry/:taskId', 'routes/entry.tsx'),
    route('checker/:taskId', 'routes/checker.tsx'),
  ]),
  route('auth', '../components/layout/AuthLayout.tsx', [route('login', 'routes/auth.login.tsx')]),
  route('icons', 'routes/icons.tsx'),
] satisfies RouteConfig
