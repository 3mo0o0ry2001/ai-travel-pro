# ✈️ AI Travel Pro: Autonomous Travel Agent

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Premium_UI-FF4B4B.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-green.svg)

An intelligent, context-aware travel assistant built to transform how users search, plan, and book their trips — powered by agentic AI reasoning and real-time flight data.

---

## 🚀 Key Features

- **🤖 Agentic Reasoning:** Powered by OpenAI's `gpt-4o-mini` with strict function-calling to make smart, multi-step travel decisions.
- **🧠 Context Injection:** Utilizes SQLite to persist personal user profiles (preferences, past trips, budgets) and inject them into every prompt.
- **🌐 Real-Time Integrations:** Connects to live flight data via **SerpApi** (Google Flights Engine) for up-to-date pricing and availability.
- **📋 Smart Watchlist:** If the cheapest flight exceeds the user's stored budget, it's automatically added to a personal watchlist for later.
- **🎨 Premium UI/UX:** A responsive, light-themed, and RTL/LTR optimized frontend built with Streamlit and custom CSS.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Core Language** | Python |
| **LLM Engine** | OpenAI API (GPT-4o-mini) |
| **Live Search** | SerpApi (Google Flights Engine) |
| **Database** | SQLite |
| **Frontend** | Streamlit |

---

## ⚙️ Installation & Setup

Want to run this project locally? Follow these steps:

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/ai-travel-pro.git
cd ai-travel-pro
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory and add your API keys:

```plaintext
OPENAI_API_KEY=your_openai_api_key_here
SERP_API_KEY=your_serpapi_key_here
```

### 4. Initialize the Database

Run the setup script to create the required SQLite tables:

```bash
python setup_db.py
```

### 5. Launch the Application

```bash
streamlit run app.py
```

---

## 📁 Project Structure

```
ai-travel-pro/
│
├── app.py          # The main Streamlit frontend application with custom CSS
├── main.py         # The core LLM agent logic and prompt engineering
├── tools.py        # Function definitions for external API calls (SerpApi, Weather, Calendar)
├── database.py     # SQLite database operations and context retrieval
└── setup_db.py     # Initialization script for database tables
```

---

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

---

## 📄 License

This project is licensed under the MIT License.

---

*Developed by **Omar Ayoub** — AI & NLP Engineer*
