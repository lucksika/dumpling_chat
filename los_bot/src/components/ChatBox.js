import React from 'react';
import bot_path from "./icons/bot.jpg";
import client_path from "./icons/client.jpg";

function Form(check, index, text) {
  if (check === "client"){
    return <div key={index} className={check}>
              <p>{text}</p>
              <img src={client_path} alt={"*"} />
           </div>
    }
  else if (check === "bot"){
    if(text != ""){
      return <div key={index} className={check}>
                <img src={bot_path} alt={"*"} />
                <p>{text}</p>
             </div>
    }
  }
}

class ChatBox extends React.Component {

  render() {
    return (
      <div>
      <div id="bot_name">
        <span>J</span>
      </div>
      <div id="chat_box">

          <br></br>
        {this.props.messages.map((message, index) => {
            return(

              Form(message.type, index, message.text)
              // <div key={index} className={message.type}>
              //   <span>{message.text}</span>
              //   <img src={bot_path} alt={"*"} />
              // </div>
            )
          })
        }

      </div>
      </div>
    )
  }
}

export default ChatBox
