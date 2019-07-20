import React from 'react';
import './App.css';
import ChatBox from './components/ChatBox';
import InputBox from './components/InputBox';

const WS = new WebSocket("ws://127.0.0.1:6789");

function str_it(dict){
  return JSON.stringify(dict);
}

function obj_it(text){
  return JSON.parse(text);
}

function sendToServer(data_obj){
  if (data_obj.text.length !== 0) {
    WS.send(str_it(data_obj));
  }
}

function clientForm(message){
  return {"type": "client", "text": message}
}

function scrollToBottom(){
  var cb = document.getElementById("chat_box");
  cb.scrollTop = cb.scrollHeight;
  console.log(cb.scrollTop, cb.scrollHeight, cb.clientHeight);
}

class App extends React.Component {

  constructor() {
    super()

    WS.onopen = function(e){
      alert("Connected to server")
    }

    let self = this;

    WS.onmessage = function incoming(server_form){
      var receive = obj_it(server_form.data)

      // console.log("FROM SERVER >>>", server_form.data)
      console.log("TEXT >>>", receive.text, receive)
      if(receive.text != ""){
        self.setState({
          messages: [...self.state.messages, receive]
        })
      }

      scrollToBottom();
    }

    WS.onclose = function(e){
        alert("Disconnected to server")
    }

    this.state = {
      messages: [
        {
          "type": "bot",
          "text": ""
          // "text": "Hi, ask me , I can speak snake snake fish fish"
        }
      ]
    }
    this.sendMessage = this.sendMessage.bind(this)
  }

  sendMessage(client_message) {
    // console.log("DATA from child to parent", client_message)
    var client_form = clientForm(client_message)
    this.setState({
      messages: [...this.state.messages, client_form]
    })
    sendToServer(client_form)
  }

  render() {
    // console.log("SETSTATE >>> ",this.state.messages);
     return (
      <div className="App">
        <ChatBox messages={this.state.messages}/>
        <InputBox sendMessage={this.sendMessage}/>

      </div>
    );
  }
}

export default App;
