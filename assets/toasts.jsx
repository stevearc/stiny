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
  return {
  }
}

const Toasts = (props) => {
  let content = props.toast ? <div className="toast">{props.toast}</div> : null
  return <div className="toasts">
    {content}
  </div>
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(Toasts)
