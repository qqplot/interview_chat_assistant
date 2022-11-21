import http from "http";
import { Server } from "socket.io";
import { instrument } from "@socket.io/admin-ui";
import express from "express";

var request = require('request');

const backend_url = "http://127.0.0.1:5000/";


const app = express();

app.set("view engine", "pug");
app.set("views", __dirname + "/views");

app.use("/public", express.static(__dirname + "/public"));
app.use(express.urlencoded({ extended: false }));
app.use(express.json());


app.get("/", (_, res) => res.render("home"));
app.post("/chat", (req, res) => {
    console.log("Init ChatRoom")
    const options = {
        method: "PUT",
        uri: backend_url + "model/interview_session/",        
        qs: {
            interview_id: req.body.roomname,
            interviewee_id: "elon_musk",
            tot_time: req.body.tottime,
        }
    };
    
    request(options, function(err, response, body) {
        if(err){
            console.log(err);
        }
        const msg = JSON.parse(body).msg;
        if(msg === "succeeded") {
            console.log(`${req.body.roomname} Room Success! tot_time: ${req.body.tottime}`);
            res.render("simple_chat", { 
                remaintime: req.body.tottime, 
                roomname: req.body.roomname,
                current_time: formatDate(new Date()),
             });
        } else {
            console.log(`${req.body.roomname} Room Failed.. Please check your Backend server.`);
            res.status(404).send('not found');
        }        
    });
});
// app.get("/*", (_, res) => res.redirect("/"));

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
    socket["nickname"] = "Anon";
    socket.onAny((event) => {
        // console.log(wsServer.sockets.adapter);
        console.log(`Socket Event:${event}`);
    });
    socket.on("enter_room",  (roomName, done) => {
        socket.join(roomName);
        done();
        socket.to(roomName).emit("welcome", socket.nickname);
        wsServer.sockets.emit("room_change", publicRooms());
    });
    socket.on("disconnecting", () => {
        socket.rooms.forEach(room => socket.to(room).emit("bye", socket.nickname));
        
    }); 
    socket.on("disconnect", () => {
        wsServer.sockets.emit("room_change", publicRooms());
    });
    socket.on("new_message", (msg, room, done) => {
        console.log(room);
        socket.to(room).emit("new_message", `${socket.nickname}:${msg}`);
        done();
    });
    socket.on("nickname", (nickname) => socket["nickname"] = nickname);
});


httpServer.listen(3000, handleListen);
