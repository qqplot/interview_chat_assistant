import http from "http";
import { Server } from "socket.io";
import { instrument } from "@socket.io/admin-ui";
import express from "express";

var request = require('request');

const app = express();

app.set("view engine", "pug");
app.set("views", __dirname + "/views");

app.use("/public", express.static(__dirname + "/public"));
app.use(express.urlencoded({ extended: false }));
app.use(express.json());


app.get("/", (_, res) => res.render("home"));
app.post("/chat", (req, res) => {
    console.log("Init ChatRoom")

    console.log(`req.body.isInterviewer: ${req.body.isInterviewer}`);

    const options = makeOption("PUT", "/model/interview_session/", {
        interview_id: req.body.roomname,
        interviewee_id: "Rachel_Lee",
        position: "Data Scientist",
        tot_time: req.body.tottime,
    });

    request(options, function(err, response, body) {
        if(err){
            console.log(err);
        }
        const msg = JSON.parse(body).msg;
        if(msg === "succeeded") {
            console.log(`${req.body.roomname} Room Success! tot_time: ${req.body.tottime}, isInterviewer: ${req.body.isInterviewer}`);
            res.render("simple_chat", { 
                remaintime: req.body.tottime, 
                roomname: req.body.roomname,
                current_time: formatDate(new Date()),
                isInterviewer: req.body.isInterviewer,
             });
        } else {
            console.log(`${req.body.roomname} Room Failed.. Please check your Backend server.`);
            res.status(404).send('not found');
        }        
    });
});

app.get("/model/question/", (req, res) => {

    const options = makeOption("GET", "/model/question/", req.query);
    console.log(options);
    request(options, function(err, response, body) {
        if(err){
            console.log(err);
        }
        console.log(body);
        let questions = JSON.parse(body);
        if(!isEmptyArr(questions)) {
            console.log(`Qeustion generation Success!`);
            res.json({ok: true, data: questions});
        } else {
            console.log(`Qeustion generation Failed..`);
            res.json({ok: false, data: []});
        }        
    });

});



app.get("/model/config/", (req, res) => {

    const options = makeOption("GET", "/model/config/", req.query);
    request(options, function(err, response, body) {
        if(err){
            console.log(err);
        }
        let config = JSON.parse(body);
        if(config) {
            console.log(`Model config get!`);
            res.json({ok: true, data: config});
        } else {
            console.log(`Model config get Failed..`);
            res.status(404).send('not found');
        }        
    });

});



function makeOption(method, uri, qs) {
    const backend_url = "http://127.0.0.1:5000";
    const url = backend_url + uri;

    return {
        method: method,
        uri: url,        
        qs: qs
    };
}



function formatDate(date) {
    const h = "0" + date.getHours();
    const m = "0" + date.getMinutes();
  
    return `${h.slice(-2)}:${m.slice(-2)}`;
  }

const handleListen = () => console.log("Listening on http://localhost:3000");

const httpServer = http.createServer(app);
const wsServer = new Server(httpServer, {
    cors: {
        origin: ["https://admin.socket.io"],
        credentials: true,
    },
});

instrument(wsServer, {
    auth: false,
});


function publicRooms() {
    const {
        sockets: {
            adapter: {sids, rooms},
        },
    } = wsServer;
    const publicRoomList = [];
    rooms.forEach((_, key) => {
        if(sids.get(key) === undefined) {
            publicRoomList.push(key);
        }
    });
    return publicRoomList;
}

wsServer.on("connection", (socket) => {
    socket["nickname"] = "You";
    socket.onAny((event) => {
        // console.log(wsServer.sockets.adapter);
        console.log(`Socket Event:${event}`);
    });
    socket.on("enter_room",  (roomName, done) => {
        socket.join(roomName);
        done();
        socket.to(roomName).emit("welcome", socket.nickname);
    });
    socket.on("disconnecting", () => {
        socket.rooms.forEach(room => socket.to(room).emit("bye", socket.nickname));        
    }); 
    socket.on("disconnect", () => {
    });
    socket.on("new_message", (msg, room, done) => {
        console.log(room);
        socket.to(room).emit("new_message", `${socket.nickname}:${msg}`);
        done();
    });
    socket.on("nickname", (nickname) => socket["nickname"] = nickname);
});

function isEmptyArr(arr) {
    if(Array.isArray(arr) && arr.length === 0)  {
      return true;
    }
    
    return false;
};


httpServer.listen(3000, handleListen);
