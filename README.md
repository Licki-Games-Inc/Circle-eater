# 🎮 Circle Eater

**Circle Eater** is a simple yet addictive Pygame project where you control a small circle and try to **eat all the moving circles as fast as possible**.  
The game features a leaderboard, difficulty settings, sound effects, and persistent settings saved between sessions.

---

## 🧩 Features

- ✅ Smooth movement and collisions  
- ✅ Win timer and automatic leaderboard tracking  
- ✅ Persistent **settings menu** (name, fullscreen, difficulty, volume, etc.)  
- ✅ Sound effects and new-record celebration  
- ✅ Clean UI with animated buttons  
- ✅ Local save files (`leaderboard.json` + `settings.json`)  
- ✅ No external dependencies beyond Pygame  

---

## 🕹️ Controls

| Key | Action |
|-----|---------|
| **Arrow Keys** | Move the player |
| **ESC** | Back / Quit |
| **ENTER / SPACE** | Select / Confirm |
| **L** | Open leaderboard (from main menu) |
| **S** | Open settings (from main menu) |
| **F** | Toggle fullscreen (in settings) |
| **D** | Cycle difficulty (in settings) |

---

## ⚙️ Settings Overview

- **Player Name** → Displays over your player and on the leaderboard  
- **Difficulty** → Changes circle speed  
  - *Easy*: Slower circles  
  - *Normal*: Default speed  
  - *Hard*: Faster circles  
- **Volume Controls** → Adjust master and SFX volumes  
- **Fullscreen Toggle** → Instantly switches between windowed and fullscreen  
- **Reset to Defaults** → Restores all settings  

Settings are stored automatically in `settings.json`.

---

## 🏆 Leaderboard

After every win:
- Your time is saved automatically under your current player name.
- The **best time** is shown at the top.
- Data is saved in `leaderboard.json`.

Press **S** in the leaderboard to toggle between **Recent** and **Best Times**.

---

## 🔊 Sound Credits

| Sound | Source |
|--------|---------|
| `pickupCoin.wav` | JFXR |
| `powerUp.wav` | JFXR |

*(You can replace these with your own sound files if you like.)*

---

## 🧠 How to Run

Make sure you have Python and Pygame installed.

```bash
pip install pygame
python main.py
```
If you have cloned this repository:
python Game_Main.py

## 🗂️ Project Structure
Circle-Eater/
├── Game_Main.py           # Main game file
├── Game_Backend.py        # Player class and related logic
├── pickupCoin.wav         # Button click sound
├── powerUp.wav            # Eat-circle sound
├── leaderboard.json       # Auto-generated leaderboard data
├── settings.json          # Auto-generated user settings
└── README.md              # You are here!

## 🚀 Future Ideas

- Multiplayer (split-screen or network)
- Enemies and power-ups
- Background music
- Online leaderboard (Firebase or Flask)
- Custom player skins / themes

## 🧑‍💻 Author
**Alexander Busk Nielsen**
Built with ❤️ using **Python** + **Pygame**
