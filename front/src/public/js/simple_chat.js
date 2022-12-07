const socket = io();

const msgerForm = get(".msger-inputarea");
const msgerInput = get(".msger-input");
const msgerChat = get(".msger-chat");

let roomName = document.getElementById("roomname").innerText;
let isInterviewer = document.getElementById("isInterviewer").innerText; 
let round = 0;
let opponent_round = 0;
let questionList = [];
let prev_question = "";
let prev_answer = "none";
let isFinished = false;

const backend_url = "http://127.0.0.1:5000/";

const BOT_MSGS = [
  "Hi, how are you?",
  "Ohh... I can't understand what you trying to say. Sorry!",
  "I like to play games... But I don't know how to play!",
  "Sorry if my answers are not relevant. :))",
  "I feel sleepy! :("
];

const APPLICANT_MSGS = [
  `Since graduating from college, I’ve had seven years of experience as a data scientist. 
  My last role at Coopang was as a principal researcher focusing on data mining utilizing R and Stata to analyze consumer data. 
  I was able to master my skills in interpreting data which would greatly benefit the team should I be granted the opportunity to work with you all. 
  I hope to progress my career in the next few years by obtaining a PhD in data science and gaining more expertise in the growing field of data analytics. 
  This next step in my career would allow me to gain experience in machine learning, analytics, and modeling in order to help the company achieve groundbreaking research in data mining.`,
  `The most recent project I worked on was with a software company. 
  My role in the project was to create and develop models then analyze customer data to create personalized product suggestions and narratives within the company's software platforms.`
];

// Icons made by Freepik from www.flaticon.com
const BOT_IMG = "https://www.svgrepo.com/show/285249/robot.svg";
const BOT_NAME = "Interview Assistant";

const PERSON_IMGS = {
  "interviewer" : "https://www.svgrepo.com/show/110198/boy.svg",
  "default" : "https://www.svgrepo.com/show/135823/boy.svg",
  "Rachel Lee" : "https://www.svgrepo.com/show/156605/girl.svg",
  "Daniel Manson" : "https://www.svgrepo.com/show/12676/boy.svg",
};

const PERSON_NAMES = {
  "default" : "You",
  "Rachel Lee" : "Rachel Lee",
  "Daniel Manson" : "Daniel Manson",
  "interviewer" : "Interviewer",
};

let nickname;
let yourImg;
let yourName;
let opponentImg;
let opponentName;


socket.emit("enter_room", roomName, initRoom);


/* Init */
function initRoom() {

  nickname = "You";
  if(isInterviewer == "yes") {
    console.log("Init Bot Message ...");
    nickname = "interviewer";
    botInitResponse();
  } else { // Applicant
    nickname = roomName;
  }

  switch(nickname) {
    case 'interviewer':  
      yourImg = PERSON_IMGS["interviewer"];
      yourName = PERSON_NAMES["default"]; // You
      opponentImg = PERSON_IMGS[roomName];
      opponentName = PERSON_NAMES[roomName];
      break;
    case 'Rachel Lee':  
      yourImg = PERSON_IMGS['Rachel Lee'];
      yourName = PERSON_NAMES['Rachel Lee']; 
      opponentImg = PERSON_IMGS["interviewer"];
      opponentName = PERSON_NAMES["interviewer"];      
      break;
    case 'Daniel Manson':  
      yourImg = PERSON_IMGS['Daniel Manson'];
      yourName = PERSON_NAMES['Daniel Manson']; 
      opponentImg = PERSON_IMGS["interviewer"];
      opponentName = PERSON_NAMES["interviewer"];    
      break;  
    default:
      yourImg = PERSON_IMGS["default"];
      yourName = PERSON_NAMES["default"]; 
      opponentImg = PERSON_IMGS["interviewer"];
      opponentName = PERSON_NAMES["interviewer"];    
      break;
  }

  socket.emit("nickname", nickname);
  msgerForm.addEventListener("submit", handleMessageSubmit);
}


function botInitResponse() {
  let msgText = "Hi, welcome to Interview Assistant! Go ahead and send me a message. &#x1F604; <br/>";
  
  msgText += `<button id="msg_init_btn">✅ Init </button>`;
  msgText += `<button id="msg_quit_btn">❌ Quit </button>`;
  appendBotMessage(BOT_NAME, BOT_IMG, "left", msgText);

  const initBtn =  document.getElementById("msg_init_btn");
  const quitBtn = get(".msg_quit_btn");
  initBtn.addEventListener("click", handleInitButtonClick);
}




function handleInitButtonClick(event) {
  event.preventDefault();
  requestQuestion();
}


socket.on("new_message", opponentResponse);

function opponentResponse(msg) {
  console.log("opponentResponse() called..");
  console.log(`isInterviewer: ${isInterviewer}`);
  const msgText = msg;
  const delay = msg.split(" ").length * 100;

  let text = msgText + "<br/>";
  if(isInterviewer === "no") {
    prev_question = msgText;
  } else {
    prev_answer = msgText;
    text += `<button type="submit" id="follow-btn-${opponent_round}" value=true>✅ follow</button>`;
    text += `<button type="submit" id="not-follow-btn-${opponent_round}" value=false>❌ not follow</button>`;  
  }

  setTimeout(() => {
    appendOpponentMessage(opponentName, opponentImg, "left", text);
    if(isInterviewer === "no") {
      console.log("Interviewer Asked You..");
    } else {
      const follow_btn = document.getElementById(`follow-btn-${opponent_round}`);
      const not_follow_btn = document.getElementById(`not-follow-btn-${opponent_round}`);
      follow_btn.addEventListener("click", handleFollowBtnClick);
      not_follow_btn.addEventListener("click", handleFollowBtnClick);
    }
    opponent_round++;
    refreshRemaintime();
  }, delay);  
}










/* Interviewer (You) */
function handleMessageSubmit(event) {
  event.preventDefault();
  const msgText = msgerInput.value;
  if (!msgText) return;

  socket.emit("new_message", msgerInput.value, roomName, () => {
      appendMessage("You", yourImg, "right", msgText);
  });
  msgerInput.value = "";
  refreshRemaintime();
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






/* BOT */
function handleQuestionSubmit(event) {
  event.preventDefault();

  var questionValue = this.querySelector('input[name="questionValue"]:checked').value;
  prev_question = questionValue;

  socket.emit("new_message", prev_question, roomName, () => {
      appendMessage(yourName, yourImg, "right", prev_question);
  });

  console.log(prev_question);
  // opponentResponse(); -> wait Response
  refreshRemaintime();  
}


function botQuestionResponse(questions) {
  console.log("botQuestionResponse() called");
  questionList = questions;
  msgText = makeList(round);

  const delay = random(1, 5) * 100;

  setTimeout(() => {
    appendBotMessage(BOT_NAME, BOT_IMG, "left", msgText);
    const botForm = document.getElementById(`form-round${round}`);
    botForm.addEventListener("submit", handleQuestionSubmit); 
    addEventPagelist(round); 
  }, delay);
}


function appendBotMessage(name, img, side, text) {
  //   Simple solution for small apps
  console.log("appendBotMessage() called");
  
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




function handleFollowBtnClick(event) {
  event.preventDefault();
  console.log("handleFollowBtnClick() called");
  requestQuestion(prev_question, prev_answer, roomName, this.value); 
}

function appendOpponentMessage(name, img, side, text) {
  //   Simple solution for small apps
  console.log("appendOpponentMessage() called");
  
  let msg_id = "opponent-" + opponent_round;  
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

function makeList(round) {
      
  let list = `<div class="question-list-wrap">`;
  list += `<form id="form-round${round}" class="question-form">`;
  list += `<ul id="question-list-round${round}" class="question-list" aria-live="polite">`
  for(let i = 0; i < questionList.length; i++) {
    list += `<li id="round${round}-order${questionList[i]['order']}">`;
    list += `<label class="question-label"><input type="radio" name="questionValue" value="${questionList[i]['question']}">`;
    list += `<div class="question-item">`
    list += `[${questionList[i]['section']}] ${questionList[i]['question']} (score: ${Math.round(questionList[i]['score'] * 100) / 100})`;
    list += `</div></label>`
    list += "</li>";    
  }
  list += "</ul>"
  list += `<button type="submit">Submit</button>`;
  list += "</form>";
  list += makePage(round);
  list += "</div>";
  
  return list;

}


function makePage(round) {
  let pagelist = `
    <button class="slide_prev_button pagination-button" id="prev-button-round${round}" title="Previous page" aria-label="Previous page">
      &lt;
    </button>
   
    <ul class="slide_pagination" id="slide_pagination-round${round}"></ul>
   
    <button class="slide_next_button pagination-button" id="next-button-round${round}" title="Next page" aria-label="Next page">
    &gt;
    </button>
  `;
  return pagelist;
}


let currentPages = [1];
let pageCounts = [0];

function addEventPagelist(round) {
  const paginationLimit = 3;
  const pageCount = Math.ceil(questionList.length / paginationLimit);

  currentPages.push(1);
  pageCounts.push(pageCount);
  let currentPage = currentPages[round];

  const paginatedList = document.getElementById(`question-list-round${round}`);
  const paginationNumbers = document.getElementById(`pagination-numbers-round${round}`);
  
  const listItems = paginatedList.querySelectorAll("li");
  const nextButton = document.getElementById(`next-button-round${round}`);
  const prevButton = document.getElementById(`prev-button-round${round}`);

  nextButton.value = round;
  prevButton.value = round;



  const pagination = document.getElementById(`slide_pagination-round${round}`);
  for (let i = 0; i < pageCount; i++) {
    if (i === 0) pagination.innerHTML += `<li class="active">•</li>`;
    else pagination.innerHTML += `<li>•</li>`;
  }
  const paginationItems = pagination.getElementsByTagName(`li`);
  console.log(paginationItems);

  const disableButton = (button) => {
    button.classList.add("disabled");
    button.setAttribute("disabled", true);
  };
  
  const enableButton = (button) => {
    button.classList.remove("disabled");
    button.removeAttribute("disabled");
  };
  
  const handlePageButtonsStatus = (round) => {
    let currentPage = currentPages[round];
    if (currentPage === 1) {
      disableButton(prevButton);
    } else {
      enableButton(prevButton);
    }
  
    if (pageCount === currentPage) {
      disableButton(nextButton);
    } else {
      enableButton(nextButton);
    }
  };
  
  const handleActivePageNumber = () => {
    document.querySelectorAll(".pagination-number").forEach((button) => {
      button.classList.remove("active");
      const pageIndex = Number(button.getAttribute("page-index"));
      if (pageIndex == currentPage) {
        button.classList.add("active");
      }
    });
  };
  

  const setCurrentPage = (pageNum, round) => {
    currentPages[round] = pageNum;
  
    handleActivePageNumber();
    handlePageButtonsStatus(round);
    
    const prevRange = (pageNum - 1) * paginationLimit;
    const currRange = pageNum * paginationLimit;
    const paginatedList = document.getElementById(`question-list-round${round}`);
    const listItems = paginatedList.querySelectorAll("li");

    listItems.forEach((item, index) => {
      item.classList.add("hidden");
      if (index >= prevRange && index < currRange) {
        item.classList.remove("hidden");
      }
    });
  };

  setCurrentPage(1, round);

  prevButton.addEventListener("click", (event) => {
    let round = event.currentTarget.value;
    const currentPage = currentPages[round] - 1;
    const pagination = document.getElementById(`slide_pagination-round${round}`);
    const paginationItems = pagination.getElementsByTagName(`li`);

    Array.from(paginationItems).forEach((i) => i.classList.remove("active"));
    paginationItems[currentPage-1].classList.add("active");

    console.log("prevButton: round-" + round + ", current page: " + currentPages[round]);
    setCurrentPage(currentPage, round);
  });

  nextButton.addEventListener("click", (event) => {
    let round = event.currentTarget.value;
    const currentPage = currentPages[round] + 1;
    const pagination = document.getElementById(`slide_pagination-round${round}`);
    const paginationItems = pagination.getElementsByTagName(`li`);

    Array.from(paginationItems).forEach((i) => i.classList.remove("active"));
    paginationItems[currentPage-1].classList.add("active");

    console.log("prevButton: round-" + round + ", current page: " + currentPages[round]);
    setCurrentPage(currentPage, round);
  });

  document.querySelectorAll(`pagination-number-round${round}`).forEach((button) => {
    const pageIndex = Number(button.getAttribute("page-index"));

    if (pageIndex) {
      button.addEventListener("click", () => {
        setCurrentPage(pageIndex);
      });
    }
  });

}



function refreshRemaintime() {
  console.log("refreshRemaintime() called");
  const remaintime = document.getElementById("remaintime");
  console.log(remaintime.innerText);

  let url = "/model/config/";
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
    if(json["ok"]) {
      remaintime.innerText = json["data"]["rem_time"] + " min";
    } else {
      console.log("refreshRemaintime() Failed...")
    }
  });

}


function requestQuestion(question, answer, interview_id=roomName, is_follow_up=false) {

  if(isFinished) {
    finishInterview();
    return;
  }

  let url = "/model/question/";
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
    if(json["ok"]) {
      botQuestionResponse(json["data"]);
    } else {
      console.log("Question generation Failed...");
      finishInterview();
    }
  });
  round++;
}


function finishInterview() {
  console.log("finishInterview() called");

  if(!isFinished) {
    isFinished = true;
    const msgText = "Interview is over. Thank you! 😀";
    const delay = 1000;
    
    setTimeout(() => {
      appendBotMessage(BOT_NAME, BOT_IMG, "left", msgText);
      refreshRemaintime();
    }, delay);
    return;
  }

}


