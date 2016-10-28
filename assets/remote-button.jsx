import React, {PropTypes} from 'react'
import "./remote-button.styl";

const RemoteButton = (props) => {
  return <button className="remote-button" onClick={props.onClick} disabled={props.disabled}>
    <span className={`icon icon-${props.image}`}></span>
  </button>
}

RemoteButton.propTypes = {
  image: PropTypes.string.isRequired,
  onClick: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
}

RemoteButton.defaultProps = {
  disabled: false,
}

export default RemoteButton
