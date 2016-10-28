// @flow
import fetch from 'isomorphic-fetch'
import {doFetch} from './util.js'
import {
  COMMAND_START, COMMAND_RESOLVE, COMMAND_ERROR,
  SIGNOUT_START, SIGNOUT_RESOLVE, SIGNOUT_ERROR,
  SIGNIN_START, SIGNIN_RESOLVE, SIGNIN_ERROR,
  GOOGLE_AUTH_SET,
  USER_SET,
  PERMISSIONS_SET,
  TOAST_ADD, TOAST_REMOVE,
} from './actionTypes.js'

export function startCommand (command: string): {
  type: string,
  name: string,
} {
  return {
    type: COMMAND_START,
    name: command,
  }
}

export function resolveCommand (command: string): {
  type: string,
  name: string,
} {
  return {
    type: COMMAND_RESOLVE,
    name: command,
  }
}

export function errorCommand (command: string, error: string): {
  type: string,
  name: string,
  error: string,
} {
  return {
    type: COMMAND_ERROR,
    name: command,
    error: error,
  }
}

function runCommand(command): Function {
  return (dispatch, getState): Promise<any> => {
    dispatch(startCommand(command))
    return doFetch(`/api/home/${command}`, {method: 'POST'})
      .then(response => {
        dispatch(resolveCommand(command))
        dispatch(addToast("unlocked!"))
      })
      .catch(err => {
        dispatch(errorCommand(command, err))
        dispatch(addToast(err))
      })
  }
}

export function unlock() {
  return (dispatch: Function, getState: Function) => {
    if (getState().command.inFlight) {
      return Promise.resolve()
    } else {
      dispatch(runCommand('unlock'))
    }
  }
}

export function signinStart() {
  return {
    type: SIGNIN_START,
  }
}

export function signinResolve (user: string, permissions: string[]) {
  return {
    type: SIGNIN_RESOLVE,
    user: user,
    permissions: permissions,
  }
}

export function signinError (error: string) {
  return {
    type: SIGNIN_ERROR,
    error: error,
  }
}

export function setGoogleAuth(auth: Object) {
  return {
    type: GOOGLE_AUTH_SET,
    auth: auth,
  }
}

export function signinWithGoogleUser(user: {getAuthResponse: Function}) {
  return (dispatch: Function, getState: Function) => {
    dispatch(signinStart())
    let token: string = user.getAuthResponse().id_token
    return doFetch('/api/login', {method: 'POST'}, {access_token: token})
      .then(response => response.json())
      .then(({user, permissions}) => dispatch(signinResolve(user, permissions)))
      .catch((err: string) => {
        dispatch(addToast(err))
        dispatch(signinError(err))
      })
  }
}

export function setUser(user: ?string) {
  return {
    type: USER_SET,
    user: user,
  }
}

export function setPermissions(permissions: string[]) {
  return {
    type: PERMISSIONS_SET,
    permissions: permissions,
  }
}

// SIGNOUT

export function signoutStart () {
  return {
    type: SIGNOUT_START,
  }
}

export function signoutResolve () {
  return {
    type: SIGNOUT_RESOLVE,
  }
}

export function signoutError (error: string) {
  return {
    type: SIGNOUT_ERROR,
    error: error,
  }
}

export function signout() {
  return (dispatch: Function, getState: Function) => {
    const state = getState()
    if (state.auth.inFlight) {
      return Promise.resolve()
    }
    dispatch(signoutStart())
    return new Promise((resolve, reject) => {
      state.auth.googleAuth.signOut().then(resolve, reject)
    }).then(() =>
      doFetch('/api/logout', {method: 'POST'})
    ).then(() => dispatch(signoutResolve()))
    .catch(err => {
      dispatch(signoutError(err))
      dispatch(addToast(err))
    })
  }
}

export function addToast(message: string, duration: number = 3000) {
  return (dispatch: Function, getState: Function) => {
    let state = getState()
    if (state.toasts.length == 0) {
      setTimeout(() => dispatch(removeToast()), duration)
    } else if (state.toasts[state.toasts.length - 1].message === message) {
      return Promise.resolve()
    }
    dispatch({
      type: TOAST_ADD,
      toast: {
        message: message,
        duration: duration,
      },
    })
    return Promise.resolve()
  }
}

export function removeToast () {
  return (dispatch: Function, getState: Function) => {
    let state = getState()
    if (state.toasts.length > 1) {
      setTimeout(() => dispatch(removeToast()), state.toasts[1].duration)
    }
    dispatch({
      type: TOAST_REMOVE,
    })
    return Promise.resolve()
  }
}
