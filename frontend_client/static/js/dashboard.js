// dashboard enhancements
// Initialize map lazily after DOM; ensure container has size
let map = L.map('map');
let followEnabled = true;
let lastTelemetryTs = null;
let lastFrameTime = null;
let frameCount = 0;
let fpsIntervalStart = performance.now();
let commandHistory = [];
let historyIndex = -1;
const metricsContainer = document.getElementById('metrics');
const connStatus = document.getElementById('connStatus');
const lastUpdateEl = document.getElementById('lastUpdate');
const latencyEl = document.getElementById('latency');
const frameAgeEl = document.getElementById('frameAge');
const videoFpsEl = document.getElementById('videoFps');
const themeToggleBtn = document.getElementById('themeToggle');
const consoleSection = document.getElementById('console');
const cameraSection = document.getElementById('camera');
const mapPanel = document.getElementById('map');
const moduleXPanel = document.getElementById('moduleX');
const attitudePanel = document.getElementById('attitude');
const horizon = document.getElementById('horizon');
const rollRead = document.getElementById('rollRead');
const pitchRead = document.getElementById('pitchRead');
const yawRead = document.getElementById('yawRead');
const altitudeScale = document.getElementById('altitude-scale');
const altitudeCurrent = document.getElementById('altitude-current');
// engine & battery elements
const rpmDeck = document.getElementById('rpmDeck');
let rpmGauges = {};
function ensureRpmGauges(count){
  const labels = ['RPM1','RPM2','RPM3','RPM4'];
  if(!rpmDeck) return;
  const existing = Object.keys(rpmGauges).length;
  if(existing >= count) return;
  for(let i=existing; i<count; i++){
    const id = 'rpm'+(i+1);
    const wrap = document.createElement('div');
    wrap.className='rpm-gauge off';
    wrap.id = id;
    // SVG circumference params
  const r = 32; // radius for 72px gauge
    const c = 2 * Math.PI * r;
    wrap.innerHTML = `\n      <svg viewBox="0 0 100 100">\n        <defs>\n          <filter id="rpmGlow" x="-50%" y="-50%" width="200%" height="200%">\n            <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="blur"/>\n            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>\n          </filter>\n        </defs>\n        <circle class="rpm-arc-bg" cx="50" cy="50" r="${r}" stroke-dasharray="${c}" stroke-dashoffset="0"/>\n        <circle class="rpm-arc" cx="50" cy="50" r="${r}" stroke-dasharray="${c}" stroke-dashoffset="${c}"/>\n      </svg>\n      <div class="rpm-text"><div class="val" id="${id}Val">--</div><div class="lbl">${labels[i]}</div></div>`;
    rpmDeck.appendChild(wrap);
    rpmGauges[id] = { el: wrap, arc: wrap.querySelector('.rpm-arc'), valEl: wrap.querySelector('.val'), circumference: c, smooth:0 };
  }
}
const batteryLevelEl = document.getElementById('batteryLevel');
const batteryTextEl = document.getElementById('batteryText');
const batteryVoltEl = document.getElementById('batteryVolt');
const batteryCurrentEl = document.getElementById('batteryCurrent');
const consoleBadge = document.getElementById('consoleBadge');
const consoleFilterSel = document.getElementById('consoleFilter');
let consoleLines = [];
function renderConsole(){
  const filter = consoleFilterSel ? consoleFilterSel.value : 'all';
  const out = document.getElementById('output');
  if(!out) return;
  out.innerHTML='';
  const frag = document.createDocumentFragment();
  consoleLines.forEach(l => {
    if(filter !== 'all' && l.sev !== filter) return;
    const div = document.createElement('div');
    div.className = 'line '+l.sev;
    div.innerHTML = `<time>${l.ts}</time>${l.text}`;
    frag.appendChild(div);
  });
  out.appendChild(frag);
  out.scrollTop = out.scrollHeight;
  if(consoleBadge) consoleBadge.textContent = consoleLines.length;
}
function classifyLine(txt){
  if(/error|fail|critical/i.test(txt)) return 'error';
  if(/warn|deprecated/i.test(txt)) return 'warn';
  return 'info';
}
function clearConsole(){ consoleLines=[]; renderConsole(); }
if(consoleFilterSel){ consoleFilterSel.addEventListener('change', renderConsole); }

// build altitude scale (relative around current)
let lastAltRendered = null;
function renderAltitudeScale(current){
  if(!altitudeScale) return;
  const step = 15; // meters per major division
  const range = 60; // +/- meters shown
  // Only rebuild if we crossed a step boundary significantly
  if(lastAltRendered !== null && Math.abs(current - lastAltRendered) < step/3) return;
  lastAltRendered = current;
  altitudeScale.innerHTML='';
  for(let d=-range; d<=range; d+=step){
    const alt = current + d;
    const y = 50 - (d / range) * 50; // percent within container
    const group = document.createElement('div');
    group.className='alt-mark';
    group.style.top = `${y}%`;
    group.innerHTML = `<span class="alt-label">${alt.toFixed(0)}</span>`;
    altitudeScale.appendChild(group);
    const line = document.createElement('div');
    line.className='alt-line';
    line.style.top = `${y}%`;
    altitudeScale.appendChild(line);
  }
}

// build pitch reference lines
(function initPitchLines(){
  const pitchLines = document.getElementById('pitch-lines');
  if(!pitchLines) return;
  for(let deg=-30; deg<=30; deg+=10){
    if(deg===0) continue;
    const line = document.createElement('div');
    line.className='p-line';
    line.style.top = `calc(50% - ${deg*2}px)`; // scale factor 2px/deg
    line.textContent = `${deg}`;
    pitchLines.appendChild(line);
  }
})();

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);

const droneIcon = L.icon({ iconUrl: '/static/device-drone-electronic-svgrepo-com.svg', iconSize: [40,40] });
const drone_m = L.marker(['-35.3','149.1'], {icon: droneIcon}).addTo(map);
let pastdata = [];

const socket = io();

// plain output console restored

function setConnected(state){
  if(state){
    connStatus.textContent = 'Connected';
    connStatus.classList.remove('disconnected');
    connStatus.classList.add('connected');
  } else {
    connStatus.textContent = 'Disconnected';
    connStatus.classList.remove('connected');
    connStatus.classList.add('disconnected');
  }
}

socket.on('connect', ()=>{ setConnected(true); });
socket.on('disconnect', ()=>{ setConnected(false); });

socket.on('drone_data', data => {
  const recvTs = performance.now();
  if(lastTelemetryTs){
    const latency = Math.round(recvTs - lastTelemetryTs.clientTsSent);
    latencyEl.textContent = `Latency: ${latency} ms`;
  }
  lastTelemetryTs = { clientTsSent: recvTs };

  metricsContainer.innerHTML = '';
  Object.entries(data.param).forEach(([k,v]) => {
    if(v === null || typeof v === 'undefined') return; // skip nulls to avoid blank tiles
    let display = v;
    if(typeof display === 'number'){
      if(Math.abs(display) >= 1000) display = display.toFixed(0);
      else if(Math.abs(display) >= 10) display = display.toFixed(1);
      else display = display.toFixed(3);
    }
    const tile = document.createElement('div');
    tile.className = 'metric-tile';
    const label = document.createElement('div'); label.className='label'; label.textContent = k;
    const value = document.createElement('div'); value.className='value'; value.textContent = display;
    tile.appendChild(label); tile.appendChild(value);
    metricsContainer.appendChild(tile);
  });

  if('altitude_msl' in data.param){
    const cur = data.param.altitude_msl;
    if(typeof cur === 'number'){
      altitudeCurrent.textContent = cur.toFixed(1)+'m';
      renderAltitudeScale(cur);
    }
  } else if('altitude' in data.param){
    const cur = data.param.altitude;
    if(typeof cur === 'number'){
      altitudeCurrent.textContent = cur.toFixed(1)+'m';
      renderAltitudeScale(cur);
    }
  }

  // attitude values
  if('roll_deg' in data.param){
    const roll = data.param.roll_deg || 0;
    const pitch = data.param.pitch_deg || 0;
    const yaw = data.param.yaw_deg || 0;
    rollRead.textContent = `Roll: ${roll.toFixed(1)}°`;
    pitchRead.textContent = `Pitch: ${pitch.toFixed(1)}°`;
    yawRead.textContent = `Yaw: ${yaw.toFixed(1)}°`;
    // transform horizon: pitch = translateY, roll = rotate
    if(horizon){
      const pitchOffset = pitch * 2; // 2px per degree
      horizon.style.transform = `translateY(${pitchOffset}px) rotate(${(-roll)}deg)`;
    }
  }

  // engine RPM SVG arcs (smooth & modern)
  const maxRpm = 10000;
  const rpmValues = [data.param.rpm1, data.param.rpm2, data.param.rpm3, data.param.rpm4].filter(v=> typeof v === 'number');
  const activeCount = Math.max(rpmValues.length, 4); // keep 4 slots
  ensureRpmGauges(activeCount);
  ['rpm1','rpm2','rpm3','rpm4'].forEach((id,idx)=>{
    const g = rpmGauges[id]; if(!g) return;
    const raw = data.param[id];
    if(typeof raw !== 'number' || isNaN(raw)) {
      g.el.classList.add('off');
      g.valEl.textContent='--';
      g.arc.style.strokeDashoffset = g.circumference;
      return;
    }
    g.el.classList.remove('off');
    // smoothing (simple low-pass)
    if(!g.smooth) g.smooth = raw; else g.smooth = g.smooth + (raw - g.smooth)*0.3;
    const val = g.smooth;
    g.valEl.textContent = Math.round(val);
    const pct = Math.max(0, Math.min(1, val / maxRpm));
    let zone = 'nominal'; if(pct > 0.9) zone='crit'; else if(pct > 0.7) zone='low';
    g.el.classList.remove('nominal','low','crit'); g.el.classList.add(zone);
    const offset = g.circumference * (1 - pct);
    g.arc.style.strokeDashoffset = offset;
  });

  // battery
  if('battery_pct' in data.param){
    const pct = data.param.battery_pct;
    if(typeof pct === 'number' && batteryLevelEl){
      const clamped = Math.max(0, Math.min(100, pct));
      batteryLevelEl.style.width = clamped + '%';
      batteryTextEl.textContent = clamped.toFixed(0) + '%';
      const shell = batteryLevelEl.closest('.battery-status');
      shell.classList.remove('low','crit');
      if(clamped <= 30 && clamped > 15) shell.classList.add('low');
      else if(clamped <= 15) shell.classList.add('crit');
    }
  }
  if('voltage' in data.param && typeof data.param.voltage === 'number'){
    batteryVoltEl.textContent = data.param.voltage.toFixed(2) + ' V';
  }
  if('current_a' in data.param && typeof data.param.current_a === 'number'){
    batteryCurrentEl.textContent = data.param.current_a.toFixed(1) + ' A';
  }

  if('lat' in data.param && 'long' in data.param){
    const lat = data.param.lat; const lon = data.param.long;
    drone_m.setLatLng([lat, lon]);
    pastdata.push([lat, lon]);
    if(pastdata.length > 2){
      L.polyline(pastdata.slice(-200), {color:'black'}).addTo(map);
    }
    if(followEnabled){ map.setView([lat, lon], 15); }
  }
  lastUpdateEl.textContent = 'Last update: just now';
  scheduleAgeUpdate();
});

socket.on('video_frame', frame_data => {
  const videoElement = document.getElementById('videoframe');
  const now = performance.now();
  lastFrameTime = now;
  frameCount++;
  if(now - fpsIntervalStart >= 1000){
    videoFpsEl.textContent = `Video: ${frameCount} fps`;
    frameCount = 0; fpsIntervalStart = now;
  }
  videoElement.src = 'data:image/jpeg;base64,' + frame_data.frame;
  frameAgeEl.textContent = 'Age: 0 ms';
});

socket.on('term_out', msg => {
  const text = msg.data;
  const sev = classifyLine(text);
  const ts = new Date().toLocaleTimeString();
  consoleLines.push({text, sev, ts});
  if(consoleLines.length > 2000) consoleLines.shift();
  renderConsole();
});

// Launch MAVProxy after DOM ready
socket.emit('term_in','mavproxy.py --master="udp:127.0.0.1:14552"');

function scheduleAgeUpdate(){
  // update last update age every second
  if(scheduleAgeUpdate._running) return;
  scheduleAgeUpdate._running = true;
  setInterval(()=>{
    if(lastTelemetryTs){
      const age = Math.round((performance.now() - lastTelemetryTs.clientTsSent));
      if(age < 1500) lastUpdateEl.textContent = 'Last update: just now';
      else lastUpdateEl.textContent = `Last update: ${(age/1000).toFixed(1)} s ago`;
    }
    if(lastFrameTime){
      const fAge = Math.round(performance.now() - lastFrameTime);
      frameAgeEl.textContent = `Age: ${fAge} ms`;
    }
  }, 1000);
}

function sendCommand(){
  const commandEl = document.getElementById('command');
  const command = commandEl.value.trim();
  if(!command) return;
  socket.emit('term_in', command);
  commandHistory.push(command);
  historyIndex = commandHistory.length;
  commandEl.value='';
}

// key handling for command history
const commandInput = document.getElementById('command');
commandInput.addEventListener('keydown', e => {
  if(e.key === 'Enter') { e.preventDefault(); sendCommand(); }
  else if(e.key === 'ArrowUp') { if(historyIndex > 0){ historyIndex--; commandInput.value = commandHistory[historyIndex] || ''; setTimeout(()=>commandInput.setSelectionRange(commandInput.value.length, commandInput.value.length),0);} e.preventDefault(); }
  else if(e.key === 'ArrowDown') { if(historyIndex < commandHistory.length -1){ historyIndex++; commandInput.value = commandHistory[historyIndex] || ''; } else { historyIndex = commandHistory.length; commandInput.value=''; } e.preventDefault(); }
});

function overlay(){ document.getElementById('scriptmodeenable').style.display='block'; }
function off(){ document.getElementById('scriptmodeenable').style.display='none'; }

function simulate(){
  const confirmRun = confirm('Run script? This will send commands to MAVProxy.');
  if(!confirmRun) return;
  var script = document.getElementById('script').value.replace(/"/g,'\\"');
  const command = `echo "${script}"| tee /home/sdbeast/script.txt >/dev/null && echo "Write operation successful." || echo "Write operation failed."`;
  socket.emit('file', command);
  socket.emit('term_in','script /home/sdbeast/script.txt');
}

function toggleFollow(){
  followEnabled = !followEnabled;
  document.getElementById('followToggle').textContent = 'Follow: ' + (followEnabled? 'ON':'OFF');
}

function toggleTheme(){
  const root = document.getElementById('content');
  const dark = root.classList.toggle('dark-mode');
  themeToggleBtn.textContent = dark ? 'Light' : 'Dark';
  localStorage.setItem('theme', dark? 'dark':'light');
}

(function restoreTheme(){
  const saved = localStorage.getItem('theme');
  if(saved === 'dark'){ document.getElementById('content').classList.add('dark-mode'); themeToggleBtn.textContent = 'Light'; }
})();

// Section toggling
const toggleLinks = document.querySelectorAll('#keys a[data-toggle]');
const sectionsMap = {
  metrics: document.getElementById('metrics'),
  camera: cameraSection,
  console: consoleSection,
  map: mapPanel,
  attitude: attitudePanel
};

function recomputeLayout(){
  const consoleHidden = consoleSection.classList.contains('toggle-hidden');
  const mapHidden = mapPanel.classList.contains('toggle-hidden');
  const hudHidden = sectionsMap.metrics.classList.contains('toggle-hidden');

  mapPanel.classList.remove('grow-full');
  consoleSection.classList.remove('grow-full');
  mapPanel.style.flex='';
  consoleSection.style.flex='';

  if(!mapHidden && consoleHidden){ mapPanel.classList.add('grow-full'); }
  else if(mapHidden && !consoleHidden){ consoleSection.classList.add('grow-full'); }
  else if(!mapHidden && !consoleHidden){ mapPanel.style.flex='2 1 0'; consoleSection.style.flex='1 1 0'; }

  if(!hudHidden && !mapHidden && consoleHidden){ mapPanel.classList.add('grow-full'); }
  // ensure Leaflet map redraw after layout mutation
  setTimeout(()=>{ if(map) map.invalidateSize(); }, 120);

  const camHidden = cameraSection.classList.contains('toggle-hidden');
  const attHidden = attitudePanel.classList.contains('toggle-hidden');
  cameraSection.classList.remove('grow-full');
  attitudePanel.classList.remove('grow-full');
  cameraSection.style.flex=''; attitudePanel.style.flex='';
  if(!camHidden && attHidden){ cameraSection.classList.add('grow-full'); }
  else if(camHidden && !attHidden){ attitudePanel.classList.add('grow-full'); }
  else if(!camHidden && !attHidden){ cameraSection.style.flex='1 1 0'; attitudePanel.style.flex='1 1 0'; }

}

toggleLinks.forEach(link => {
  link.addEventListener('click', () => {
    const target = link.getAttribute('data-toggle');
    if(!target) return;
    const el = sectionsMap[target.toLowerCase()];
    if(el){
      el.classList.toggle('toggle-hidden');
      link.classList.toggle('active');
      recomputeLayout();
    }
  });
});

recomputeLayout();
// initial map sizing correction shortly after load
setTimeout(()=>{ if(map) map.invalidateSize(); }, 300);

// expose for inline buttons
window.sendCommand = sendCommand;
window.overlay = overlay;
window.off = off;
window.simulate = simulate;
window.toggleFollow = toggleFollow;
window.toggleTheme = toggleTheme;
window.clearConsole = clearConsole;