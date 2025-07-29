# Dronacharya 🚁

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.5+-red.svg)](https://opencv.org/)
[![MAVLink](https://img.shields.io/badge/MAVLink-Compatible-orange.svg)](https://mavlink.io/)

A comprehensive drone control and monitoring system with real-time face detection, tracking capabilities, and MAVLink integration. Features a modern Flask-based web interface with live video streaming, telemetry data visualization, and an integrated web terminal for drone command execution.

## ✨ Features

- 🎥 **Real-time Video Streaming**: Live camera feed with face detection overlay
- 👤 **Face Recognition**: Advanced face detection and recognition using OpenCV
- 🛰️ **MAVLink Integration**: Full drone telemetry and control via MAVLink protocol
- 🌐 **Web Interface**: Modern, responsive web dashboard
- 💻 **Integrated Terminal**: Web-based terminal for direct drone commands
- 📊 **Telemetry Display**: Real-time altitude, speed, GPS, and battery monitoring
- 🎯 **SITL Compatible**: Works with ArduPilot Software-In-The-Loop simulation

## 📁 Project Structure

```
dronacharya/
├── frontend_client/           # Main Flask application
│   ├── main.py               # Original application file
│   ├── new_main.py           # Enhanced main application with web terminal
│   ├── cam.py                # Camera handling utilities
│   ├── Face_Recog.py         # Face recognition logic
│   ├── Face_Trainer.py       # Face training utilities
│   ├── templates/            # HTML templates
│   ├── static/              # CSS, JS, and static assets
│   ├── output-face-ymls/    # Face recognition models
│   └── haarcascade_frontalface_default.xml  # OpenCV face detection model
├── mcp-server/              # Model Context Protocol server
│   ├── main.py             # MCP server implementation
│   ├── mcp_server.py       # Server logic
│   └── pyproject.toml      # MCP project configuration
├── terrain/                 # Terrain data files
├── requirements.txt         # Python dependencies
├── imp_cmd.txt             # Important commands reference
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- ArduPilot SITL (for simulation)
- Webcam (for face detection)
- Git

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Somanath-03/Dronacharya.git
   cd Dronacharya
   ```

2. **Create and activate virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Linux/Mac
   # or
   venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### 🛩️ Running with SITL Simulation

1. **Start ArduPilot SITL**

   ```bash
   sim_vehicle.py -v copter --console --map -w --out 127.0.0.1:14551 --out 127.0.0.1:14552
   ```

2. **Connect MAVProxy (optional)**

   ```bash
   mavproxy.py --master=udp:127.0.0.1:14552
   ```

3. **Run the application on a seperate terminal**

   ```bash

   cd frontend_client/
   python3 new_main.py
   ```

4. **Access the web interface**
   Open your browser and navigate to `http://127.0.0.1:5000`

## 🎯 Key Components

### Web Dashboard

- **Live Video Feed**: Real-time camera stream with face detection overlays
- **Telemetry Panel**: Live display of altitude, speed, GPS coordinates, battery status
- **Interactive Map**: GPS position visualization
- **Web Terminal**: Direct command interface for drone control

### Face Detection & Recognition

- **Real-time Detection**: Uses Haar Cascade classifiers for face detection
- **Recognition System**: Trained models for person identification
- **Overlay Graphics**: Visual indicators on detected faces

### MAVLink Integration

- **Telemetry Streaming**: Real-time data from VFR_HUD and GPS_RAW_INT messages
- **Command Interface**: Send commands directly to the autopilot
- **SITL Compatible**: Full integration with ArduPilot SITL simulation

### Mission Control Protocol (MCP)

- **Server Implementation**: Advanced mission control capabilities
- **Navigation Interface**: Integration with mapping services for route planning

## 🔧 Configuration

### Important Ports

- **SITL Output**: 14551, 14552 (UDP)
- **Web Interface**: 5000 (HTTP)
- **MAVLink Connection**: 127.0.0.1:14552

### Key Files

- `frontend_client/new_main.py` - Main application with enhanced features
- `requirements.txt` - Python dependencies
- `imp_cmd.txt` - Important commands reference

## 📱 Usage

1. **Start the system** following the Quick Start guide
2. **Access the web interface** at `http://127.0.0.1:5000`
3. **Monitor telemetry** in real-time on the dashboard
4. **Use the web terminal** for direct drone commands:
   ```
   mode stabilize
   arm throttle
   takeoff 10
   mode guided
   guided -45.363261 149.165230 100
   ```

## 🛠️ Development

### Adding New Features

- Face recognition models are stored in `output-face-ymls/`
- Web interface templates are in `frontend_client/templates/`
- Static assets (CSS, JS) are in `frontend_client/static/`

### Training Face Recognition

```bash
python3 frontend_client/Face_Trainer.py
```

### MCP Server Development

The MCP server is located in `mcp-server/` and provides advanced mission control capabilities.

## 🙏 Acknowledgments

- [ArduPilot](https://ardupilot.org/) - Open source autopilot system
- [OpenCV](https://opencv.org/) - Computer vision library
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [MAVLink](https://mavlink.io/) - Communication protocol for drones


**⚠️ Safety Notice**: Always follow local regulations and safety guidelines when operating drones. This software is for educational and research purposes.
