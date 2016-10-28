// @flow
import {
  COMMAND_START, COMMAND_RESOLVE, COMMAND_ERROR,
  SIGNOUT_START, SIGNOUT_RESOLVE, SIGNOUT_ERROR,
  SIGNIN_START, SIGNIN_RESOLVE, SIGNIN_ERROR,
  GOOGLE_AUTH_SET,
  USER_SET,
  PERMISSIONS_SET,
  TOAST_ADD, TOAST_REMOVE,
} from './actionTypes.js'

export function auth(state: {
  user: ?string,
  googleAuth: ?Object,
  inFlight: boolean,
  permissions: string[],
} = {
  user: null,
  googleAuth: null,
  inFlight: false,
  permissions: [],
}, action: Object) {
  switch (action.type) {
    case GOOGLE_AUTH_SET:
      return {...state,
        googleAuth: action.auth,
      }
    case USER_SET:
      return {...state,
        user: action.user,
      }
    case PERMISSIONS_SET:
      return {...state,
        permissions: action.permissions,
      }
    case SIGNOUT_START:
      return {...state,
        inFlight: true,
      }
    case SIGNOUT_RESOLVE:
      return {...state,
        inFlight: false,
        user: null,
        googleUser: null,
        permissions: [],
      }
    case SIGNOUT_ERROR:
      return {...state,
        inFlight: false,
      }
    case SIGNIN_START:
      return {...state,
        inFlight: true,
      }
    case SIGNIN_RESOLVE:
      return {...state,
        inFlight: false,
        user: action.user,
        permissions: action.permissions,
      }
    case SIGNIN_ERROR:
      return {...state,
        inFlight: false,
      }
    default:
      return state
  }
}

export function command(state: {
  inFlight: boolean,
  name: ?string,
} = {
  inFlight: false,
  name: null,
}, action: Object) {
  switch (action.type) {
    case COMMAND_START:
      return {...state,
        inFlight: true,
        name: action.name,
      }
    case COMMAND_RESOLVE:
    case COMMAND_ERROR:
      return {...state,
        inFlight: false,
      }
    default:
      return state
  }
}

export function toasts(state: {
  message: string,
  duration: number,
}[] = [], action: Object) {
  switch (action.type) {
    case TOAST_ADD:
      return [...state, action.toast]
    case TOAST_REMOVE:
      return state.slice(1)
    default:
      return state
  }
}
