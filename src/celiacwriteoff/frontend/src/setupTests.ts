import '@testing-library/jest-dom'
import { afterEach, beforeEach, vi } from 'vitest'

// AuthProvider (src/context/AuthContext.tsx) calls fetch('/auth/me') as soon
// as it mounts, to check whether there's an existing session. There's no
// real backend in tests, so without a default mock that call would reject
// and print an unhandled-rejection warning in every test that renders
// AuthProvider (directly, or via renderWithProviders in test-utils.tsx).
// This default treats every test as starting logged-out (a 401 response),
// which is the right default for most page tests. A test that needs a
// signed-in user, or needs to assert on a specific request, should
// override this with its own vi.mock/vi.spyOn on fetch.
beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(() => Promise.resolve(new Response(null, { status: 401 }))),
  )
})

afterEach(() => {
  vi.unstubAllGlobals()
})
