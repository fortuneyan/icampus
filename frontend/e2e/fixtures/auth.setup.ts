import { test as setup, expect } from '@playwright/test'
import path from 'path'

const authFile = path.join(__dirname, '.auth', 'admin.json')

setup('authenticate as admin', async ({ request }) => {
  const response = await request.post('/api/v1/auth/login', {
    data: {
      username: 'admin',
      password: 'admin123',
    },
  })

  expect(response.ok()).toBeTruthy()

  const body = await response.json()
  const accessToken = body.access_token

  await request.storageState({
    path: authFile,
    cookies: [],
    origins: [],
  })

  // 手动构建 storageState，将 token 注入 localStorage
  const storageState = {
    cookies: [],
    origins: [
      {
        origin: 'http://localhost:5173',
        localStorage: [
          {
            name: 'token',
            value: accessToken,
          },
        ],
      },
    ],
  }

  const fs = await import('fs')
  fs.mkdirSync(path.dirname(authFile), { recursive: true })
  fs.writeFileSync(authFile, JSON.stringify(storageState, null, 2))
})

export default {
  storageState: 'e2e/fixtures/.auth/admin.json',
}
