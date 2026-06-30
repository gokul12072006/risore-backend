# Risore AI - Your Personal Local AI Assistant

An advanced, highly capable, completely free, and open-source local AI assistant designed to be lightning-fast and secure. Risore serves as your interactive companion for productivity, tech, fitness, and more!

## 🚀 Features
- **Smart Modular Architecture**: Built-in specialized modules for Tech, Fitness, App Development, Education, Daily Life, and Recommendations.
- **Risore 1.0 AI Engine**: Features a humble, dynamic AI personality that mirrors your prompt length. Offers deep expertise in Business, Stock Market Analysis, Cryptocurrency, and Gaming (including Steam offers & monitoring).
- **Dynamic Graphic Messages**: Automatically generates engaging visual infographics when real-time data is unavailable, avoiding dead links and keeping the experience interactive.
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

**Using the Cinematic Web Platform**
1. Start the secure backend API server:
`venv\Scripts\python.exe server.py`
2. Open `web/index.html` in your favorite web browser!

*Other specific CLI modules:*
- `.\risore.bat tech "Write a Python script to scrape a website"`
- `.\risore.bat fitness "Create a 3-day home workout plan"`

## 🧠 Teaching Risore
To teach Risore new skills or provide it with private data:
1. Place your text, PDF, or markdown files into the `risore_storage/data/` folder (or via the Web UI).
2. The data is permanently embedded into the local ChromaDB vector database. Risore will automatically use this knowledge in future conversations.

---

