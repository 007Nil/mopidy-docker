# Mopidy Docker (ALSA Enabled)

A production-ready Dockerized Mopidy setup with:

- 🎵 Local library support  
- 🔊 Native ALSA hardware audio output  
- 🐳 Docker Compose orchestration  
- 🛠 Automatic local scan on startup  
- 📦 Clean infra-ready structure  

Designed for Debian-based systems with direct sound card access.

---

## 🚀 Overview

This project provides a reproducible, hardware-enabled Mopidy deployment using Docker.

Unlike most Mopidy containers, this setup:

- Supports **direct ALSA output (hw device)**
- Works with real sound cards (`/dev/snd`)
- Handles correct audio group permissions
- Separates build, config, and runtime state cleanly

Tested on:
- Debian (Bookworm)
- Thin client / dedicated media servers

---

## 📁 Project Structure

```text
mopidy-docker/
├── bootstrap.sh
├── docker-compose.yml
├── README.md
├── mopidy-src/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── mopidy/
│   ├── mopidy-local/
│   └── mopidy-requirements.txt
├── config/
│   └── mopidy.conf
├── data/        (runtime state)
└── cache/       (runtime cache)
