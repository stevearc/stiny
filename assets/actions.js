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

export function startCommand (command) {
  return {
    type: COMMAND_START,
    name: command,
  }
}

export function resolveCommand (command) {
  return {
    type: COMMAND_RESOLVE,
    name: command,
  }
}

export function errorCommand (command, error) {
  return {
    type: COMMAND_ERROR,
    name: command,
    error: error,
  }
}

function runCommand(command) {
  return (dispatch, getState) => {
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
  return (dispatch, getState) => {
    if (getState().command.inFlight) {
      return Promise.resolve()
    } else {
      dispatch(runCommand('unlock'))
    }
  }
}

export function signinStart () {
  return {
    type: SIGNIN_START,
  }
}

export function signinResolve (user, permissions) {
  return {
    type: SIGNIN_RESOLVE,
    user: user,
    permissions: permissions,
  }
}

export function signinError (error) {
  return {
    type: SIGNIN_ERROR,
    error: error,
  }
}

export function setGoogleAuth(auth) {
  return {
    type: GOOGLE_AUTH_SET,
    auth: auth,
  }
}

export function signinWithGoogleUser(user) {
  return (dispatch, getState) => {
    dispatch(signinStart())
    let token = user.getAuthResponse().id_token
    return doFetch('/api/login', {method: 'POST'}, {access_token: token})
      .then(response => response.json())
      .then(({user, permissions}) => dispatch(signinResolve(user, permissions)))
      .catch(err => {
        dispatch(addToast(err))
        dispatch(signinError(err))
      })
  }
}

export function setUser(user) {
  return {
    type: USER_SET,
    user: user,
  }
}

export function setPermissions(permissions) {
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

export function signoutError (error) {
  return {
    type: SIGNOUT_ERROR,
    error: error,
  }
}

export function signout() {
  return (dispatch, getState) => {
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

export function addToast(message, duration=3000) {
  return (dispatch, getState) => {
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

export function removeToast (toast) {
  return (dispatch, getState) => {
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
