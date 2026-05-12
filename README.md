# 🦄 Desktop Pet

Animated desktop companion built with Python and Tkinter.

A lightweight desktop pet featuring autonomous behaviors, animated GIF rendering with transparency, draggable interactions and a simple state machine architecture.

---

## ✨ Features

- 🎞️ Animated GIF rendering with native transparency
- 🖱️ Draggable desktop companion
- 🚶 Autonomous random walking behavior
- 🦘 Smooth jumping animation with parabola motion
- 🧠 State machine architecture (`IDLE`, `WALK`, `JUMP`, `DRAG`)
- 📌 Optional always-on-top mode
- 📏 Dynamic resizing from context menu
- 🧹 Safe resource cleanup
- ⚡ Lightweight and simple

---

## 🛠️ Technologies

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/Tkinter-FFCC00?style=for-the-badge&logo=python&logoColor=black)
![Pillow](https://img.shields.io/badge/Pillow-8A2BE2?style=for-the-badge)
![GIF Animation](https://img.shields.io/badge/GIF-Animation-ff69b4?style=for-the-badge)

---

## 🧱 Architecture

The project is organized into modular components:

| Component | Responsibility |
|---|---|
| `VideoPlayer` | GIF animation playback |
| `WindowManager` | Window transparency and geometry |
| `BehaviorEngine` | Autonomous behavior state machine |
| `DesktopPet` | Main application orchestration |

---

## 🎮 Controls

| Action | Behavior |
|---|---|
| Left Click + Drag | Move pet |
| Right Click | Open menu |
| Double Click | Close application |

---

## 🚀 Run the project

```bash
pip install pillow
python main.py

📸 Preview

<img width="360" height="269" alt="image" src="https://github.com/user-attachments/assets/f0b7a7c6-fb90-4d77-aae9-3cdee1f04fd8" />
<img width="290" height="187" alt="image" src="https://github.com/user-attachments/assets/548980a1-470e-4e4b-af9d-c1f745d743fd" />


## 🌱 Future Ideas
Sound effects
Multiple pets
Idle animations
Custom skins
Physics interactions
AI-powered interactions

## 👩‍💻 Author
Created by FatiVilla

Passionate about software development, automation and creative technology.
