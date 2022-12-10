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
let isWait = false;
let summaryList = [];

// Icons made by Freepik from www.flaticon.com
const BOT_IMG = "https://www.svgrepo.com/show/285249/robot.svg";
const BOT_NAME = "Interview Assistant";

const PERSON_IMGS = {
  "interviewer" : "https://www.svgrepo.com/show/362184/user-male.svg",
  "default" : "https://www.svgrepo.com/show/135823/boy.svg",
  "Rachel Lee" : "https://www.svgrepo.com/show/156605/girl.svg",
  "Daniel Manson" : "https://www.svgrepo.com/show/12676/boy.svg",
};

const PERSON_NAMES = {
  "default" : "Anonymous",
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
socket.on("new_message", opponentResponse);

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
      yourName = "You"; // You
      let check_name = "default";
      if(roomName === "Rachel Lee" || roomName === "Daniel Manson") {
        check_name = roomName;
      }
    
      opponentImg = PERSON_IMGS[check_name];
      opponentName = roomName;
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
  
  msgText += `<button id="msg_init_btn">✅ Init </button>&nbsp`;
  msgText += `<button id="msg_quit_btn">❌ Quit </button>`;
  appendBotMessage(BOT_NAME, BOT_IMG, "right", msgText);

  const initBtn = document.getElementById("msg_init_btn");
  const quitBtn = document.getElementById("msg_quit_btn");
  initBtn.addEventListener("click", handleInitButtonClick);
  quitBtn.addEventListener("click", handleQuitButtonClick);
  round++;
}

function handleQuitButtonClick(event) {
  event.preventDefault();
  const initBtn =  document.getElementById("msg_init_btn");
  const quitBtn = document.getElementById("msg_quit_btn");
  initBtn.setAttribute('disabled', 'disabled');
  quitBtn.setAttribute('disabled', 'disabled');
  alert("Quit. Thank you!!");
  finishInterview();
}


function handleInitButtonClick(event) {
  event.preventDefault();
  const initBtn =  document.getElementById("msg_init_btn");
  const quitBtn = document.getElementById("msg_quit_btn");
  initBtn.setAttribute('disabled', 'disabled');
  quitBtn.setAttribute('disabled', 'disabled');
  requestQuestion();
}




async function opponentResponse(msg) {
  console.log(`opponentResponse() called.. isInterviewer: ${isInterviewer}`);

  const msgText = msg;
  const delay = msg.split(" ").length * 10;

  const promise = new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve("done");
    }, delay)
  });
  await promise;
  if(isInterviewer === "yes") waitResponse(opponent_round);

  let remaintime = document.getElementById("remaintime");
  let text = msgText + "<br/>";
  if(isInterviewer === "no") {
    prev_question = msgText;
  } else {
    prev_answer = msgText;
    const time = remaintime.innerText.split(' ')[0];
    if(time > 0) {
      text += `<button type="submit" id="follow-btn-${opponent_round}" value=true>✅ follow</button>&nbsp`;
      text += `<button type="submit" id="not-follow-btn-${opponent_round}" value=false>❌ not follow</button>`;  
    }
  }

  appendOpponentMessage(opponentName, opponentImg, "left", text);  

  if(isInterviewer === "no") {
    console.log("Interviewer Asked You..");
  } else {
    const follow_btn = document.getElementById(`follow-btn-${opponent_round}`);
    const not_follow_btn = document.getElementById(`not-follow-btn-${opponent_round}`);
    if(!isEmpty(follow_btn)) {
      follow_btn.addEventListener("click", handleFollowBtnClick);
      not_follow_btn.addEventListener("click", handleFollowBtnClick);      
    } else {
      finishInterview();
    }
  }
  opponent_round++;
  refreshRemaintime();
}










/* Interviewer (You) */
function handleMessageSubmit(event) {
  event.preventDefault();
  const msgText = msgerInput.value;
  if(!msgText) return;

  if(msgText.trim() === "quit()") {
    finishInterview(); 
  }

  socket.emit("new_message", msgerInput.value, roomName, () => {
      appendMessage("You", yourImg, "right", msgText);
  });
  msgerInput.value = "";
  this.setAttribute('disabled', 'disabled');
  refreshRemaintime();
}


function appendMessage(name, img, side, text) {
  //   Simple solution for small apps
  let msg_id = "bot-" + round;
  const msgHTML = `
    <div class="msg ${side}-msg choice" id="${msg_id}">
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

  console.log("handleQuestionSubmit() called..");

  var questionValue = this.querySelector('input[name="questionValue"]:checked').value;
  prev_question = questionValue;
  
  socket.emit("new_message", prev_question, roomName, () => {
      appendMessage(yourName, yourImg, "right", prev_question);
  });

  console.log(prev_question);
  var submitBtn = this.querySelector('.submitBtn');

  submitBtn.setAttribute('disabled', 'disabled');
  document.getElementsByTagName('button');
  // opponentResponse(); -> wait Response
  const delay = random(1, 5) * 300;
  setTimeout(() => {
    waitResponse(opponent_round);
  }, delay);
  
  refreshRemaintime();  
}

function waitResponse(id) {
  
  let text;
  if(!isWait) {
    isWait = true;
    text = `<div class='wait-maker' style="text-align: center;">`;
    text += `<img class="blinking" src="https://www.svgrepo.com/show/157949/microphone.svg" width="50" height="50" border="0"></img>`;
    text += "</div>"
    appendOpponentMessage(opponentName, opponentImg, "left", text);
    return;
  }
  
  let msg_id = "opponent-" + id;    

  const msg_text = document.getElementById(msg_id);
  // msg_text.style.display = 'none';
  msg_text.remove();
  isWait = false;
}



function botQuestionResponse(questions) {
  console.log("botQuestionResponse() called");
  questionList = questions;
  msgText = makeList(round);

  const delay = random(1, 5) * 100;

  setTimeout(() => {
    appendBotMessage(BOT_NAME, BOT_IMG, "right", msgText);
    const botForm = document.getElementById(`form-round${round}`);
    botForm.addEventListener("submit", handleQuestionSubmit); 
    addEventPagelist(round); 
    round++;
  }, delay);
}


function appendBotMessage(name, img, side, text) {
  //   Simple solution for small apps
  console.log("appendBotMessage() called");
  
  let msg_id = "bot-" + round;  
  const msgHTML = `
    <div class="msg ${side}-msg bot" id="${msg_id}">
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

  this.setAttribute('disabled', 'disabled');

  let btnId = this.id;
  if(this.value === "true") { // follow
    btnId = "not-" + btnId;
  } else {
    btnId = btnId.substring(4);
  }
  document.getElementById(btnId).setAttribute('disabled', 'disabled');
  requestQuestion(prev_question, prev_answer, roomName, this.value); 
}

function appendOpponentMessage(name, img, side, text) {
  //   Simple solution for small apps
  let msg_id = "opponent-" + opponent_round;  
  console.log(`appendOpponentMessage() called... msg_id: ${msg_id}`);

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
    list += `<div class="question-item">`;

    if(questionList[i]['score'] > 2000) {
      list += `<b>[${questionList[i]['section']}]</b>&nbsp`;
      list += `<button type="button" class="btn btn-danger">Follow-up</button>`;
      list += "<br/>";
    } else if(questionList[i]['score'] > 1000) {
      list += `<b>[${questionList[i]['section']}]</b>&nbsp`;
      list += `<button type="button" class="btn btn-primary">CV</button>&nbsp`;
      list += `<button type="button" class="btn btn-success">JD</button>`;
      list += "<br/>";
    } else {
      list += `<b>[${questionList[i]['section']}]</b><br/>`;
    }
    
    list += ` ${questionList[i]['question']} (score: ${Math.round(questionList[i]['score'] * 100) / 100})`;
    list += `</div></label>`
    list += "</li>";    
  }
  list += "</ul>"
  list += `<button type="submit" class="submitBtn">Submit</button>`;
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
  // console.log(paginationItems);

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
  console.log(`Remain time: ${remaintime.innerText}`);

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
  // round++;
}




function finishInterview() {
  console.log("finishInterview() called");

  if(!isFinished) {
    isFinished = true;
    let text = "Interview is over. Thank you! 😀<br/>";

    if(round > 0) {
      text += `<button id="btn-modal">📃 Your Summary</button>`;
    }
    
    const delay = 1000;
    // const config = getConfig();

    setTimeout(() => {
      appendBotMessage(BOT_NAME, BOT_IMG, "right", text);
      refreshRemaintime();
      if(round > 0) {
        getSummary();
        const smryBtn = document.getElementById("btn-modal");
        smryBtn.setAttribute('disabled', 'disabled');
        smryBtn.addEventListener("click", handleGetSummaryBtn);

      }
    }, delay);
    return;
  }

}

function getSummary() {
  console.log("getSummary() called");
  let url = "/model/summary/";
  async function request() {
    const response = await fetch(url,
    {
      method: 'GET',
      Origin: 'http://localhost:3000'
    });
    return response;
  }
  const smryBtn = document.getElementById("btn-modal");

  request()
  .then(res => res.json())
  .then(json => {    
    if(json["ok"]) {
      summaryList = json['data'];      

      setTimeout(() => {
        smryBtn.removeAttribute('disabled');
      }, 5000);
      return summaryList;
    } else {
      console.log("getSummary() Failed...")
    }
  });

}



function getConfig() {
  console.log("getConfig() called");
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
      return json["data"];
    } else {
      console.log("getConfig() Failed...")
    }
});
}




function isEmpty(value) {
  if( value == "" || value == null || value == undefined ){
    return true
  } else {
    return false
  }
};


function handleGetSummaryBtn(event) {
  event.preventDefault();

  const modalHTML = makeSummaryList();
  const modal = document.getElementById("modal"); 
  modal.innerHTML = modalHTML;

  function modalOn() {
    modal.style.display = "flex";
  }

  function isModalOn() {
    return modal.style.display === "flex";
  }

  function modalOff() {
    modal.style.display = "none";
  }

  const btnModal = document.getElementById("btn-modal");
  btnModal.addEventListener("click", modalOn);

  const closeBtn = modal.querySelector(".close-area");
  closeBtn.addEventListener("click", modalOff);
  modal.addEventListener("click", e => {
    const evTarget = e.target
    if(evTarget.classList.contains("modal-overlay")) {
        modalOff();
    }
  });

  window.addEventListener("keyup", e => {
    if(isModalOn() && e.key === "Escape") {
        modalOff();
    }
  });

}




function makeSummaryList() {
  let list = "";
  list += `<div class="modal-window">
  <div class="title"> 
    <h2> Interview Summary </h2>
  </div>
  <div class="close-area">X</div>
  <div class="content">
  `;

  list += `<table class="summary-table" border="1">
    <thead>
      <tr>
        <th scope="col">Type</th>
        <th scope="col">Content</th>
        <th scope="col">Section</th>
        <th scope="col">Source</th>
        <th scope="col">Score</th>
      </tr>
    </thead><tbody>`;
  for(let i = 0; i < summaryList.length; i++) {
    if((i % 2) == 0) { // Question
      list += `<tr>`;
      list += `<th scope="row">Q</th>`;
      list += `<td>${summaryList[i]["question"]}</td>`;
      list += `<td>${summaryList[i]["section"]}</td>`;
      list += `<td>${summaryList[i]["source"]}</td>`;
      list += `<td>${Math.round(summaryList[i]["score"] * 100) / 100}</td>`;
      list += "</tr>";
    } else { //Answer
      list += `<tr>`;
      list += `<th scope="row">A</th>`;
      list += `<td class="even">${summaryList[i]["answer"]}</td>`;
      list += `<td class="even"></td>`;
      list += `<td class="even"></td>`;
      list += `<td class="even"></td>`;
      list += "</tr>";
    }        
  }
  list += "</tbody></table>"
  list += "</div></div>";

  return list;
}