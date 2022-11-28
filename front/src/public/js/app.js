// const test_btn = document.getElementById("test_btn");

// test_btn.addEventListener("click", renderPagination);

function requestQuestion() {

    let url = "/model/question/";
  
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
        console.log(json);
    });

};
  
function renderPagination(currentPage) {
    if (_totalCount <= 20) return; 
  
    var totalPage = Math.ceil(_totalCount / 20);
    var pageGroup = Math.ceil(currentPage / 10);
  
    var last = pageGroup * 10;
    if (last > totalPage) last = totalPage;
    var first = last - (10 - 1) <= 0 ? 1 : last - (10 - 1);
    var next = last + 1;
    var prev = first - 1;
  
    const fragmentPage = document.createDocumentFragment();
    if (prev > 0) {
      var allpreli = document.createElement('li');
      allpreli.insertAdjacentHTML("beforeend", `<a href='#js-bottom' id='allprev'>&lt;&lt;</a>`);
  
      var preli = document.createElement('li');
        preli.insertAdjacentHTML("beforeend", `<a href='#js-bottom' id='prev'>&lt;</a>`);
  
        fragmentPage.appendChild(allpreli);
        fragmentPage.appendChild(preli);
    }
    
    for (var i = first; i <= last; i++) {
      const li = document.createElement("li");
      li.insertAdjacentHTML("beforeend", `<a href='#js-bottom' id='page-${i}' data-num='${i}'>${i}</a>`);
      fragmentPage.appendChild(li);
    }
  
    if (last < totalPage) {
      var allendli = document.createElement('li');
      allendli.insertAdjacentHTML("beforeend", `<a href='#js-bottom'  id='allnext'>&gt;&gt;</a>`);
  
      var endli = document.createElement('li');
      endli.insertAdjacentHTML("beforeend", `<a  href='#js-program-detail-bottom'  id='next'>&gt;</a>`);
  
      fragmentPage.appendChild(endli);
      fragmentPage.appendChild(allendli);
    }
  
  
    document.getElementById('js-pagination').appendChild(fragmentPage);
    // 페이지 목록 생성
  
    document.querySelectorAll(`#js-pagination a`).removeClass("active");
    document.querySelectorAll(`#js-pagination a#page-${currentPage}`).addClass("active");
  
    document.querySelectorAll("#js-pagination a").click(function (e) {
      e.preventDefault();
      var $item = $(this);
      var $id = $item.attr("id");
      var selectedPage = $item.text();
  
      if ($id == "next") selectedPage = next;
      if ($id == "prev") selectedPage = prev;
      if ($id == "allprev") selectedPage = 1;
      if ($id == "allnext") selectedPage = totalPage;
  
      list.renderPagination(selectedPage);//페이지네이션 그리는 함수
      list.search(selectedPage);//페이지 그리는 함수
    });
  };
// const socket = io();
// const welcome = document.getElementById("welcome");
// const form = document.querySelector("form");
// const room = document.getElementById("room");

// room.hidden = true;

// let roomName;

// function addMessage(msg) {
//     const ul = room.querySelector("ul");
//     const li = document.createElement("li");
//     li.innerText = msg;
//     ul.appendChild(li);
// }

// function backendDone(msg) {
//     console.log(`The backend says:`, msg);
// }

// function handleMessageSubmit(event) {
//     event.preventDefault();
//     const input = room.querySelector("#msg input");
//     const value = input.value;
//     socket.emit("new_message", input.value, roomName, () => {
//         addMessage(`You: ${value}`);
//     });
//     input.value = "";
// }

// function handleNicknameSubmit(event) {
//     event.preventDefault();
//     const input = room.querySelector("#name input");
//     socket.emit("nickname", input.value);
//     input.value = "";

// }


// function showRoom() {
//     welcome.hidden = true;
//     room.hidden = false;
//     const h3 = room.querySelector("h3");
//     h3.innerText = `Room ${roomName}`;
//     const msgForm = room.querySelector("#msg");
//     const nameForm = room.querySelector("#name");
//     msgForm.addEventListener("submit", handleMessageSubmit);
//     nameForm.addEventListener("submit", handleNicknameSubmit);
// }

// function handleRoomSubmit(event) {
//     event.preventDefault();
//     const input = form.querySelector("input");
//     socket.emit("enter_room", input.value, showRoom);
//     roomName = input.value;
//     input.value = "";
// }

// form.addEventListener("submit", handleRoomSubmit);

// socket.on("welcome", (user) => {
//     addMessage(`${user} joined!`);
// });

// socket.on("bye", (left) => {
//     addMessage(`${left} left..`);
// });

// socket.on("new_message", addMessage);

// socket.on("room_change", (rooms) => {
//     console.log(welcome);
//     const roomList = welcome.querySelector("ul");
//     roomList.innerHTML = "";
//     if(rooms.lengths === 0) {
//         return;
//     }
    
//     rooms.forEach((room) => {
//         const li = document.createElement("li");
//         li.innerText = room;
//         roomList.append(li);
//     });
// });

