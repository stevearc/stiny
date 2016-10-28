// @flow
import React from 'react'
import RemoteButton from './remote-button.jsx'
import LoginButton from './login-button.jsx'
import {connect} from 'react-redux'
import {unlock, signout, signinWithGoogleUser, addToast} from './actions.js'
import {hasPermission} from './util.js'
import './home.styl';


const mapStateToProps = (state, ownProps) => {
  return {
    disableButtons: state.command.inFlight,
    showLogin: state.auth.user == null,
    canUnlock: hasPermission(state, 'unlock'),
  }
}

const mapDispatchToProps = (dispatch, ownProps) => {
  return {
    onUnlock: () => dispatch(unlock()),
    onSignout: () => dispatch(signout()),
    onSignin: result => dispatch(signinWithGoogleUser(result)),
    onSigninFailure: result => dispatch(addToast("Google signin failed")),
  }
}

const Home = (props) => {
  let login = null
  if (props.showLogin) {
    login = <LoginButton scope="email" longtitle={true} width={300} height={50} theme="dark"
      onSuccess={props.onSignin} onFailure={props.onSigninFailure} />
  } else {
    login = <div className="logout">
      <a onClick={props.onSignout}>Sign out</a>
    </div>
  }
  return <div className="home">
    {login}
    {props.canUnlock ?  <RemoteButton image="unlocked" onClick={props.onUnlock}
        disabled={props.disableButtons}/> : null
    }
  </div>
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(Home)
