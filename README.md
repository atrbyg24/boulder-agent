# 🧗‍♂️ BoulderAgent: AI-Powered Trip Planner

**BoulderAgent** is an intelligent assistant designed to help climbers plan their outdoor sessions (currently focused on the Powerlinez and the Gunks). It combines a local climbing database with real-time weather forensics to answer the questions such as: *"Is it dry enough to send?"* or *"What grade is Oliphant Crack?"*

## ✨ Features
* **Natural Language Database Queries**: Ask questions like *"How many V3s are at the Welcome Boulders?"* 
* **Weather Forensics**: Automatically checks 48-hour precipitation history and "Send Temps" (35°F - 60°F) for specific GPS coordinates.
* **Function Calling**: Powered by Gemini 2.5 Flash, the agent intelligently decides when to query the SQL database or check the weather API.
* **Safety Logic**: Uses a "Green/Yellow/Red" status system to warn users about wet rock or dangerous conditions.
* **Observability**: Built-in tracing to monitor AI "Chain of Thought" and tool-calling accuracy.

## 🛠 Tech Stack
* **AI Model**: Google Gemini (via the `google-genai` SDK)
* **Database**: SQLite (Climbing data provided by [OpenBeta](https://openbeta.io))
* **Weather API**: [Open-Meteo](https://open-meteo.com) (Historical and Forecast data)
* **Environment**: Python 3.12+

## 🚀 Getting Started

### 1. Clone & Install
```bash
git clone https://github.com/atrbyg24/boulder-agent.git
cd boulder-agent
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file in the root directory. Do not commit this file to GitHub.

```plaintext
GEMINI_API_KEY=your_api_key_here
```

### 3. Run the Agent

```bash
python main.py
```

## 📊 Data Sources & Credits
This project would not be possible without the following open-data providers:

* **[OpenBeta](https://openbeta.io)**: For providing the comprehensive, open-source climbing dataset (routes, grades, and coordinates).
* **[Open-Meteo](https://open-meteo.com)**: For the high-resolution weather API that allows for historical precipitation and hourly forecast lookups without an API key for non-commercial use.

## ⚠️ Disclaimer

Climbing is inherently dangerous. BoulderAgent is an experimental tool and should not be your only source of safety information. Always check local conditions in person and respect all access closures.