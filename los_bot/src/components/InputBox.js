import React from 'react';

class InputBox extends React.Component {

  constructor() {
    super()
    this.state = {
      message: ""
    }
    this.handleChange = this.handleChange.bind(this)
    this.handleSubmit = this.handleSubmit.bind(this)
  }

  handleChange(e) {
    console.log(e.target.value)
    this.setState({
      message: e.target.value
    })
  }

  handleSubmit(e) {
    e.preventDefault()
    console.log(this.state.message)
    this.props.sendMessage(this.state.message)
    this.setState({
      message: ""
    })
  }

  render() {
    return (
      <form id="input_box" onSubmit={this.handleSubmit}>
        <input id="client_input" type="text" value={this.state.message} name="clientInput" placeholder="Type something..."
          onChange={this.handleChange} autoComplete="off"></input>
      </form>
    )
  }

}

export default InputBox
