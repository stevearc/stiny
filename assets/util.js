// @flow

export function getCookieValue(a: string): string {
    let b = document.cookie.match('(^|;)\\s*' + a + '\\s*=\\s*([^;]+)')
    return b ? b.pop() : ''
}

export function doFetch(url: string, options: Object = {}, data: ?Object): Promise<Object> {
  if (!options.headers) {
    options.headers = new Headers()
  }
  if (data) {
    options.headers.append('content-type', 'application/json')
    options.body = JSON.stringify(data)
  }
  options.headers.append('X-CSRF-Token', getCookieValue('CSRF-Token'))
  options.credentials = 'include'
  return fetch(url, options).then((response) => {
    if (response.status != 200) {
      return response.json()
        .then(({error, msg, stacktrace}) => {
          let errMsg = `${error}: ${msg}`
          if (stacktrace) {
            console.error(stacktrace)
          } else {
            console.error(errMsg)
          }

          return Promise.reject(errMsg)
        })
    } else {
      return response
    }
  })
}

export function hasPermission(state: Object, permission: string): boolean {
  if (state.auth.permissions.includes('admin')) {
    return true
  } else {
    return state.auth.permissions.includes(permission)
  }
}

export function getMetaContent(name: string): ?string {
  let el: HTMLElement = document.head.querySelector(`meta[name='${name}']`)
  return el ? el.getAttribute('content') : null
}
