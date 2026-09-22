import { useEffect } from 'react'
import { prefetchPages } from '../routes/pageLoaders'

// Safari has no requestIdleCallback, so a short timer stands in for it there.
function whenIdle(task: () => void): () => void {
  if (typeof window.requestIdleCallback === 'function') {
    const id = window.requestIdleCallback(task)
    return () => window.cancelIdleCallback(id)
  }
  const id = window.setTimeout(task, 2000)
  return () => window.clearTimeout(id)
}

function isDataSaverOn(): boolean {
  const connection = (navigator as Navigator & { connection?: { saveData?: boolean } }).connection
  return connection?.saveData === true
}

// Downloads the login/register/profile code while the browser is idle after the
// page has loaded, so tapping "Log in" doesn't wait for a download. Skipped for
// visitors with data saver on; they still get the hover/touch prefetch on links.
export function usePrefetchAuthPages() {
  // Waiting for the browser's idle time is syncing with an external scheduler,
  // so this can't be render-time or event-handler logic.
  useEffect(() => {
    if (isDataSaverOn()) return
    return whenIdle(() => prefetchPages('login', 'register', 'profile'))
  }, [])
}
