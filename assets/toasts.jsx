// @flow
import React from 'react'
import {connect} from 'react-redux'
import {unlock} from './actions.js'
import './toasts.styl'


const mapStateToProps = (state, ownProps) => {
  return {
    toast: state.toasts.length ? state.toasts[0].message : null,
  }
}

const mapDispatchToProps = (dispatch, ownProps) => {
  return {}
}

const Toasts = (props: {
  toast: ?string
}) => {
  return <div className="toasts">
    {props.toast ? <div className="toast">{props.toast}</div> : null}
  </div>
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(Toasts)
