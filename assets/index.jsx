import React from 'react'
import {render} from 'react-dom'
import {Provider} from 'react-redux'
import thunkMiddleware from 'redux-thunk'
import {createStore, combineReducers, applyMiddleware} from 'redux'
import * as reducers from './reducers.js'
import {setUser, setGoogleAuth, setPermissions} from './actions.js'
import App from './app.jsx'
import {getMetaContent} from './util.js'
import './icons/style.css'

function startApp(auth) {
  let store = createStore(
    combineReducers(reducers),
    applyMiddleware(thunkMiddleware)
  )
  store.dispatch(setGoogleAuth(auth))

  let user = getMetaContent('stiny-user')
  store.dispatch(setUser(user))
  let perms = getMetaContent('stiny-permissions')
  if (perms) {
    store.dispatch(setPermissions(perms.split(',')))
  }

  render(
    <Provider store={store}>
      <App />
    </Provider>,
    document.getElementById('react-app')
  )
}

if (window.gapi) {
    gapi.load('auth2', () => gapi.auth2.init().then(startApp))
} else {
  window.onLoad = () => gapi.load('auth2', () => gapi.auth2.init().then(startApp))
}
