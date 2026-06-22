# Risore AI - Your Personal Local AI Assistant

An advanced, highly capable, completely free, and open-source local AI assistant designed to be lightning-fast and secure. Risore serves as your interactive companion for productivity, tech, fitness, and more!

## 🚀 Features
- **Smart Modular Architecture**: Built-in specialized modules for Tech, Fitness, App Development, Education, Daily Life, and Recommendations.
- **Real-Time Web Search**: Automatically pulls live data from DuckDuckGo when you ask about the weather, news, or current events.
- **Conversational Memory**: Remembers previous context during your chat sessions for a seamless human-like flow.
- **Zero-Cost Hybrid Cloud**: Runs locally with Ollama (Qwen 3B), uses Groq for blazing speed, and falls back to a free open-source cloud cluster so it *never* crashes.
- **Interactive CLI & Dashboard**: Chat with Risore directly in your terminal, or use the beautiful web UI!

## 🛠️ Installation & Setup
I have created a 1-click automated setup!

1. Clone this repository.
2. Double click **`setup.bat`**. This will automatically build your environment and install dependencies.
3. You're done!

## 🤖 How to Use

**Using the CLI (Terminal)**
Run the main file to enter an interactive session:
`.\risore.bat chat`

*Other specific modules:*
- `.\risore.bat tech "Write a Python script to scrape a website"`
- `.\risore.bat fitness "Create a 3-day home workout plan"`
- `.\risore.bat study "Explain the theory of relativity simply"`

**Using the Web Dashboard**
`venv\Scripts\python.exe app.py`

## 🧠 Teaching Risore
To teach Risore new skills or provide it with private data:
1. Place your text, PDF, or markdown files into the `risore_storage/data/` folder (or via the Web UI).
2. The data is permanently embedded into the local ChromaDB vector database. Risore will automatically use this knowledge in future conversations.

---
*Architected by Antigravity.*
