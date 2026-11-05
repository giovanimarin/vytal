// Shared in-flight promise for one logical session; HTTP lives in the adapter.
export function createSessionRefresh() {
  let active: { key: string; promise: Promise<void> } | null = null
  return (key: string, renew: () => Promise<void>): Promise<void> => {
    if (active?.key === key) return active.promise
    const promise = Promise.resolve().then(renew)
    active = { key, promise }
    void promise.finally(() => { if (active?.promise === promise) active = null }).catch(() => {})
    return promise
  }
}
