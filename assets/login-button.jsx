// @flow
import React, {PropTypes} from 'react'
import {findDOMNode} from 'react-dom'

class LoginButton extends React.Component {
  static defaultProps: {}

  componentDidMount() {
    this._renderGoogleButton()
  }

  componentDidUpdate() {
    this._renderGoogleButton()
  }

  _renderGoogleButton() {
    let options = {...this.props}
    delete options.id
    window.gapi.signin2.render(this.props.id, options)
  }

  render() {
    return <div id={this.props.id}></div>
  }
}

LoginButton.propTypes = {
  id: PropTypes.string,
  scope: PropTypes.string,
  width: PropTypes.number,
  height: PropTypes.number,
  longtitle: PropTypes.bool,
  theme: PropTypes.oneOf(['light', 'dark']),
  onSuccess: PropTypes.func,
  onFailure: PropTypes.func,
}

LoginButton.defaultProps = {
  id: 'login-button'
}

export default LoginButton
