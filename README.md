# RepScheduler

A local-first Windows tray app that reminds you to move.

RepScheduler runs quietly in the background and interrupts long computer sessions with randomized bodyweight exercise prompts.

Built with Python and wxPython.

No cloud.  
No telemetry.  
All data stays on your machine.

---

## What It Does (v1)

- Runs in the system tray
- Triggers exercise reminders on a fixed interval
- Supports difficulty profiles (Easy / Medium / Hard)
- Randomizes exercises and rep counts within profile limits
- Stores basic data locally in JSON

This is the foundation version.

---

## Why This Exists

Long uninterrupted screen time is physically expensive.

RepScheduler acts as a lightweight scheduling layer for basic physical maintenance.  
Not a fitness tracker.  
Not a social app.  
Not a productivity cult tool.

Just structured interruption.

---

## Privacy

RepScheduler:
- Makes zero network requests
- Collects no analytics
- Sends no data anywhere
- Stores everything locally

The project is fully open source. Audit it yourself.

---

## Installation

Clone the repository:
```
git clone https://github.com/FlossyFish63943/RepScheduler.git
cd RepScheduler
```
Create a virtual environment:
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
Run the app:
```
python main.py
```
---

## Roadmap

Planned for future versions:

- Performance trend graph & dashboard
- Daily random challenge mode
- Anti-skip interval adjustment
- Focus-aware detection
- Time-of-day intensity scaling
- Sound profiles per difficulty
- Skip limits per difficulty
- AFK logging
- Expanded user personalization inputs

---

## Version

Current: v1.0

This release focuses on core scheduling and UI stability.  
Adaptive and statistical features are coming next.

---

## Tech Stack

- Python
- wxPython

---

## License

MIT License