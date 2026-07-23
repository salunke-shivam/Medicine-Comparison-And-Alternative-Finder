# 💊 Medicine Comparison and Alternative Finder (India)

A simple AI-powered tool that helps users search for medicine information,
compare compositions, and find Indian pharmacy prices — all in one place.

Built using Python, LangGraph, Groq AI, and Streamlit.

---

## 📸 Demo

> Enter a medicine name → Get description, composition, price comparison, and alternatives instantly.

---

## 🚀 Features

- 🔍 Search any medicine by name
- 📋 Get medicine description and uses
- 🧪 View active and inactive ingredients
- ⚖️ Compare brand vs generic composition
- 💰 Find approximate Indian prices (1mg, PharmEasy, Netmeds, Jan Aushadhi)
- 🏥 See medicine alternatives with prices
- 🌐 Data from FDA, RxNorm, and web search
- 🤖 AI-powered report generation using Groq

---

## 🛠️ Tech Stack

| Tool            | Purpose                              |
|-----------------|--------------------------------------|
| Python          | Main programming language            |
| Streamlit       | Frontend user interface              |
| LangGraph       | AI agent workflow                    |
| Groq API        | LLM for generating reports           |
| LangChain       | Tools and LLM integration            |
| DuckDuckGo      | Web search for prices and extra info |
| OpenFDA API     | Medicine description and composition |
| RxNorm API      | Medicine alternatives                |

---

## 📁 Project Structure
- medicine-finder/
- │
- ├── app.py # main application file
- ├── .env # api keys (not uploaded to github)
- ├── .env.example # example env file for reference
- ├── requirements.txt # all required packages
- └── README.md # this file


---

## ⚙️ Setup and Installation

### Step 1 - Clone the repository

```bash
git clone https://github.com/salunke-shivam/Medicine-Comparison-And-Alternative-Finder.git
cd Medicine-Comparison-And-Alternative-Finder
```
Step 2 - Create a virtual environment
```Bash

python -m venv venv
```
Activate it:

On Windows:

```Bash

venv\Scripts\activate
```
On Mac/Linux:

```Bash

source venv/bin/activate
```
Step 3 - Install required packages
```Bash

pip install -r requirements.txt
```
Step 4 - Get your Groq API key
- Go to https://console.groq.com
- Create a free account
- Generate an API key
Step 5 - Create your .env file
- Create a file called .env in the project folder and add:
``` Bash
GROQ_API_KEY=your_groq_api_key_here
```
Step 6 - Run the application
```Bash

streamlit run app.py
The app will open in your browser at http://localhost:8501
```

🔄 How It Works
The app uses a LangGraph workflow where each step runs one after another:

text

User enters medicine name
         │
         ▼
- Step 1: OpenFDA API
        Gets medicine description, purpose, warnings
         │
         ▼
- Step 2: RxNorm API
        Gets medicine ID and alternative medicines
         │
         ▼
- Step 3: Composition Search
        Gets active and inactive ingredients
         │
         ▼
- Step 4: Indian Price Search
        Searches 1mg, PharmEasy, Netmeds, Jan Aushadhi via DuckDuckGo
         │
         ▼
- Step 5: Extra Search (only if FDA data is missing)
        DuckDuckGo general search
         │
         ▼
- Step 6: Groq AI
        Combines all data and generates the final report
         │
         ▼
- Final Report shown on Streamlit UI
