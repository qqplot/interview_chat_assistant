const socket = io();

const msgerForm = get(".msger-inputarea");
const msgerInput = get(".msger-input");
const msgerChat = get(".msger-chat");
let roomName = document.getElementById("roomname").innerText;
let round = 0;
let questionList = [];
let isFollowUp = false;

const backend_url = "http://127.0.0.1:5000/";

const BOT_MSGS = [
  "Hi, how are you?",
  "Ohh... I can't understand what you trying to say. Sorry!",
  "I like to play games... But I don't know how to play!",
  "Sorry if my answers are not relevant. :))",
  "I feel sleepy! :("
];

// Icons made by Freepik from www.flaticon.com
const BOT_IMG = "https://www.svgrepo.com/show/285249/robot.svg";
const PERSON_IMG = "https://www.svgrepo.com/show/110198/boy.svg";
const BOT_NAME = "Interview Assistant";
const PERSON_NAME = "You";

socket.emit("enter_room", roomName, initRoom);

function initRoom() {

  msgerForm.addEventListener("submit", handleMessageSubmit);

}



function requestQuestion(question, answer, interview_id=roomName, is_follow_up=false) {
  
  let url = backend_url + "model/question/";
  let options;
  if(round == 0) {
    options = {
      interview_id: interview_id,
      is_follow_up: is_follow_up,
    };
  } else {
    options = {
      question: question,
      answer: answer,
      interview_id: interview_id,
      is_follow_up: is_follow_up,
    };
  }

  let data = Object.entries(options);
  data = data.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`);
  
  let query = data.join('&');
  url = url + "?" + query;
  console.log(url);

  async function request() {
    const response = await fetch(url,
    {
      method: 'GET',
      Origin: 'http://localhost:3000'
    });
    return response;

  }
  
  request()
  .then(res => res.json())
  .then(json => {    
    botQuestionResponse(json);
  });

}

function botQuestionResponse(questions) {
  const r = random(0, BOT_MSGS.length - 1);
  const msgText = BOT_MSGS[r];
  const delay = msgText.split(" ").length * 100;

  setTimeout(() => {
    appendBotMessage(BOT_NAME, BOT_IMG, "left", msgText, questions);
  }, delay);
}

function handleMessageSubmit(event) {
  event.preventDefault();
  const msgText = msgerInput.value;
  if (!msgText) return;

  switch(msgText) {
    case '1':
      requestQuestion();
      break;
  
    case '2':
      requestAny();
      break;
  
    default:
      requestQuestion();      
      break;
  }

  socket.emit("new_message", msgerInput.value, roomName, () => {
      appendMessage(PERSON_NAME, PERSON_IMG, "right", msgText);
  });
  msgerInput.value = "";
  // botResponse();
}

function requestAny() {
  console.log("call 'requestAny()'...");
  let msg_id = "bot-" + 0;
  document.getElementById(msg_id).style.display = "none";
}


function appendMessage(name, img, side, text) {
  //   Simple solution for small apps
  let msg_id = "bot-" + round;
  const msgHTML = `
    <div class="msg ${side}-msg" id="${msg_id}">
      <div class="msg-img" style="background-image: url(${img})"></div>

      <div class="msg-bubble">
        <div class="msg-info">
          <div class="msg-info-name">${name}</div>
          <div class="msg-info-time">${formatDate(new Date())}</div>
        </div>

        <div class="msg-text">${text}</div>
      </div>
    </div>
  `;

  msgerChat.insertAdjacentHTML("beforeend", msgHTML);
  msgerChat.scrollTop += 500;
}

function appendBotMessage(name, img, side, text, questions) {
  //   Simple solution for small apps
  console.log("appendBotMessage() called");
  questionList = questions;
  let msg_id = "bot-" + round;
  console.log(questionList);

  text += "<br/>";
  text += `<ul class="lists">`;
  for(var qes of questionList) {    
    text += `<li class="lists__item js-load">${qes['question']}</li>`;
  }
  text += `</ul>`;
  const msgHTML = `
    <div class="msg ${side}-msg" id="${msg_id}">
      <div class="msg-img" style="background-image: url(${img})"></div>

      <div class="msg-bubble">
        <div class="msg-info">
          <div class="msg-info-name">${name}</div>
          <div class="msg-info-time">${formatDate(new Date())}</div>
        </div>

        <div class="msg-text">${text}</div>
      </div>
    </div>
  `;

  msgerChat.insertAdjacentHTML("beforeend", msgHTML);
  msgerChat.scrollTop += 500;
}

function botResponse() {
  const r = random(0, BOT_MSGS.length - 1);
  const msgText = BOT_MSGS[r];
  const delay = msgText.split(" ").length * 100;
  

  setTimeout(() => {
    appendBotMessage(BOT_NAME, BOT_IMG, "left", msgText);
  }, delay);
}



// function botResponse() {
//   const r = random(0, BOT_MSGS.length - 1);
//   const msgText = BOT_MSGS[r];
//   const delay = msgText.split(" ").length * 100;

//   setTimeout(() => {
//     appendMessage(BOT_NAME, BOT_IMG, "left", msgText);
//   }, delay);
// }

// Utils
function get(selector, root = document) {
  return root.querySelector(selector);
}

function formatDate(date) {
  const h = "0" + date.getHours();
  const m = "0" + date.getMinutes();

  return `${h.slice(-2)}:${m.slice(-2)}`;
}

function random(min, max) {
  return Math.floor(Math.random() * (max - min) + min);
}
