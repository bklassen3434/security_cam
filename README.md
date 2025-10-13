# 🧠 SecurityCam – AI-Powered Home Security System

A fully local, privacy-preserving home security stack that uses **computer vision** to detect motion, recognize faces, and send alerts via **Telegram** (or SMS).  
It exposes a **Flask API** for viewing events, and includes a **React Native iOS app** for browsing snapshots and metadata.

---

## ⚙️ Features

- 🔍 **Motion + Face Detection** using OpenCV + InsightFace  
- 👤 **Face Recognition** (whitelist of trusted faces)
- 🚨 **Telegram Alerts** for unknown faces (replaces SMS)
- 📸 **Event Logging** with timestamps, distances, bounding boxes
- 🧱 **Local Flask API** (`/api/events`) to serve data & images
- 📱 **React Native App** (iOS) for viewing events & snapshots
- 🐳 **Docker Compose Deployment** for always-on operation
- 🎥 Supports **USB webcams** or **RTSP IP cameras**

---

## 📂 Project Structure

```text
security-cam/
├── app/
│ ├── api.py # Flask API (serves events & images)
│ ├── main.py # Core vision loop (motion + face)
│ ├── face.py # Face detection & embedding
│ ├── video.py # Video input (USB / RTSP)
│ ├── notifier.py # Telegram alerts
│ ├── storage.py # Save snapshots & CSV logs
│ ├── worker.py # Entrypoint for Docker worker
│ └── ...
│
├── data/
│ ├── enroll/ # Reference images of trusted faces
│ └── events/ # Snapshots & events.csv
│
├── models/ # InsightFace model cache
│
├── mobile-native/ # React Native iOS app (runs via Xcode)
│
├── config.yaml # Local config (camera, thresholds, etc.)
├── requirements.txt # Python deps for local dev
├── requirements.docker.txt
├── Dockerfile
├── docker-compose.yml
├── wsgi.py # Gunicorn entrypoint
└── README.md
```

---

## 🐳 Docker Deployment
Runs continuously on a Raspberry Pi or mini PC.

```bash
docker compose build
docker compose up -d
```
Services
- worker – motion + face loop
- api – Flask server at http://<device-ip>:5000

All events and images are stored in ./data/events.

## 📱 iOS App (React Native CLI + Xcode)
Setup
Open mobile-native/ios/SecurityCamMobile.xcworkspace in Xcode.

Plug in your iPhone → set Team (free Apple ID) → Run.

Edit mobile-native/src/config.js:
```bash
export const BACKEND_URL = "http://<device-ip>:5000";
export const API_KEY = "<optional-key>";
```
Features
Lists all events from Flask API

Tap an event for full image + details

Works locally on your Wi-Fi or over Tailscale VPN

## 🔒 API Overview
Endpoint: Description
- /healthz:	Simple ping
- /api/events:	JSON list of recent events
- /events/<filename>:	Serves snapshot images

All data lives locally — no cloud upload required.

## 🧱 Production Tips
Use a Raspberry Pi 4 or small mini-PC (Ubuntu, Docker Compose).

Keep show_window: false for headless operation.

Expose only on your LAN or use Tailscale for secure remote access.

Use environment variable SECURITYCAM_API_KEY to protect the API.

Add a daily cleanup cron job for old events (example script: scripts/cleanup_events.py).

## 🧰 Hardware Options
Component:	Example
- Brain:	Raspberry Pi 4 (4 GB) or Intel NUC
- Camera:	USB webcam (e.g. Logitech C270) or RTSP IP camera
- Power:	Pi USB-C supply + 32 GB micro-SD
- Network:	Wi-Fi or Ethernet (same network as your phone)

## 🪄 Useful Commands
view running containers
```bash
docker compose ps
```

follow logs
```bash
docker compose logs -f worker
docker compose logs -f api
```

rebuild and restart
```bash
docker compose down && docker compose build && docker compose up -d
```
## 🧠 Acknowledgements
OpenCV

InsightFace

Flask

React Native

Docker Compose

## 🪪 License
MIT License.