// leflet
var map = L.map("map");
const commandInput = document.getElementById("command");

L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution:
    '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);

const droneIcon = L.icon({
  iconUrl: './static/device-drone-electronic-svgrepo-com.svg',
  iconSize: [40, 40],
});

var markeroptions = {
  draggable : false,
  rotationangle: 90
}

const drone_m = L.marker(
  ["-35.3","149.1"], 
  {icon: droneIcon},
).addTo(map);

var pastdata = []

// socketio
const socket = io.connect();

document.addEventListener("DOMContentLoaded", () => {
  const socket = io.connect();

  // Listen for 'drone_data' event
  socket.on("drone_data", function (data) {
    out_param = document.getElementById(
      "altitude"
    );
    out_param.innerHTML = ""
    Object.keys(data.param).forEach(key => {
      out_param.innerHTML += (`${key}: ${data.param[key]}<br>`);
    });

    // drone marker which updates
    drone_m.setLatLng([data.param['lat'], data.param['long']]);
    // update map view acc to the parameter
    map.setView([data.param['lat'], data.param['long']] , 15);
    // L.polyline(data.param['targetline'],{color:'red'}).addTo(map);
    
    pastdata.push([data.param['lat'], data.param['long']])
    if(pastdata.length>4){
      L.polyline(pastdata, {color: 'black'}).addTo(map);
    } 

  });

  // Listen for 'video_frame' event
  socket.on("video_frame", function (frame_data) {
    const videoElement = document.getElementById("videoframe");
    videoElement.src = "data:image/jpeg;base64," + frame_data.frame;
  });

  // Listen for 'terminal' event
  socket.on('term_out', function(msg) {
    document.getElementById('output').innerHTML += msg.data + '<br>';
    var outputDiv = document.getElementById('output');
    outputDiv.scrollTop = outputDiv.scrollHeight; // Auto scroll to the bottom
  });

  socket.emit('term_in','mavproxy.py --master="udp:127.0.0.1:14552"')
});


function sendCommand() {
  const command = document.getElementById('command').value;
  socket.emit('term_in', command);
  document.getElementById('command').value = '';
}

// Add event listener for the Enter key
document.getElementById('command').addEventListener('keydown', function(event) {
  if (event.key === 'Enter') {
      sendCommand();
      event.preventDefault(); // Prevent form submission if inside a form
  }
});

function overlay(){
  var element = document.getElementById("scriptmodeenable");
  element.style.display = "block";
}

function off() {
  document.getElementById("scriptmodeenable").style.display = "none";
}

function simulate(){
  var script = document.getElementById("script").value
  script = `echo "${script}"| tee /home/sdbeast/script.txt >/dev/null && echo "Write operation successful." || echo "Write operation failed."`
  socket.emit('file',script);
  socket.emit('term_in','script /home/sdbeast/script.txt');
}