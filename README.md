# 🤖 Communication and Converter System

Welcome to the source code repository developed by the Yaskawa intern team.  
This system converts DXF files into JBI format, prepared specifically for an industrial pantograph system.

You will also find here all the necessary files to build and run the app containerized with Docker 🐳, enabling portability and easy deployment.

---

## 🪛 Project Overview

The project is divided into three main parts:

- 💻 **Frontend**  
  The user interface to operate the robot. Users can log in and control the system.  
  Default roles include:  
  - **Admin** — full access to all tools and features.  
  - **Operator** — limited access focused on operation, monitoring, and diagnostics.

- 🗄️ **Backend**  
  Handles the logic to convert DXF files into JBI format, perform alarm data analysis, and send files to the robot.

- 👓 **YMConnect**  
  A C# API enabling real-time communication with the robot, supporting diagnostics and process execution.

---

## 🧩 Technology Stack

- 🐍 **FastAPI** (Python)  
- 📤 **FTP** (File Transfer Protocol)  
- 🪛 **Robots from Yaskawa Motoman Robotics**  
- 🕸️ **ReactJS**  
- ⚙️ **.NET 8** (ASP.NET Web API)  
- 🔌 **TCP/IP** (Robot communication)  
- 🗼 **YMConnect v1.1.3** — [GitHub Release](https://github.com/Yaskawa-Global/YMConnect/releases/tag/v1.1.3)  
- 🐳 **Docker** (Containerization)

---

## 🚀 How to run with Docker

1. Just run the file named "install.bat", once you have done it, you can run the app with "run.bat" everytime you require it.
2. Now you can access to the project on Docker Desktop and start the services there or initialize the project from a Windows Terminal using: **docker-compose up**, in the project root folder.
