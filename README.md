# ✈️ AI Travel Pro: Autonomous Travel Agent

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Premium_UI-FF4B4B.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-green.svg)

An intelligent, context-aware travel assistant built to transform how users search, plan, and budget for trips. **AI Travel Pro** goes beyond standard flight search engines by utilizing Agentic AI to reason through user constraints, check real-time data, and seamlessly inject user preferences into the decision-making process.

## 🚀 Key Features

* **🤖 Agentic Reasoning:** Powered by OpenAI's `gpt-4o-mini` with strict function-calling. The agent autonomously decides when to trigger external tools (e.g., searching flights vs. checking weather).
* **🧠 Context Injection:** Utilizes SQLite to persist personal user profiles (preferred airlines, seating, and budget limits). The agent invisibly reads this context to personalize every response.
* **🌤️ Real-Time Integrations:** Connects to live flight data via **SerpApi (Google Flights)** and factors in destination weather conditions before confirming travel plans.
* **📉 Smart Watchlist:** If the cheapest flight exceeds the user's stored budget, the AI proactively suggests adding the route to a database watchlist for future price monitoring.
* **🎨 Premium UI/UX:** A responsive, light-themed, and RTL/LTR optimized front-end built with Streamlit and custom CSS for a SaaS-like experience.

## 🛠️ Tech Stack

* **Core Language:** Python
* **LLM Engine:** OpenAI API (GPT-4o-mini)
* **Live Search:** SerpApi (Google Flights Engine)
* **Database:** SQLite
* **Frontend:** Streamlit 

## ⚙️ Installation & Setup

Want to run this project locally? Follow these steps:

**1. Clone the repository:**
```bash
git clone [https://github.com/YOUR_USERNAME/ai-travel-pro.git](https://github.com/YOUR_USERNAME/ai-travel-pro.git)
cd ai-travel-pro```

**2. Install dependencies:**
```bash
pip install -r requirements.txt```
