# Food Support AI Agent

## Project Overview
An intelligent customer support chatbot for food delivery platforms that can handle order tracking, refunds, and FAQ queries using Google Gemini AI and RAG.

---

## Problem Statement
Food delivery apps receive thousands of repetitive customer queries daily - order status checks, refund requests, and policy questions. Manual customer support is expensive and doesn't scale. We needed a solution that could handle these common queries automatically while providing accurate, contextual responses.

---

## Solution Summary
I built a web-based AI support agent that combines Google Gemini's language capabilities with a FAISS vector database for semantic search. When customers ask questions, the system either retrieves relevant FAQ information or performs specific actions like order tracking and refund processing. The agent can understand natural language and respond appropriately without human intervention.

---

## Tech Stack
- **Backend:** Python, FastAPI
- **Frontend:** HTML/CSS/JavaScript
- **Database / Vector DB:** FAISS
- **LLM / AI Models:** Google Gemini 2.5 Flash
- **Cloud / Hosting:** Render
- **Version Control:** Git + GitHub

---

## Project Structure
```
root/
├── app/                    # core backend code
│   ├── main.py            # FastAPI application
│   ├── gemini_agent.py    # AI agent logic
│   ├── tools.py          # function calling tools
│   └── rag_engine.py     # FAISS RAG system
├── data/                  # JSON databases
│   ├── faqs.json
│   ├── order_database.json
│   └── restaurant_data.json
├── static/               # frontend files
│   └── index.html
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Setup Instructions
Follow these exact steps to run your project locally.
```bash
# 1. Clone the repository
git clone https://github.com/Hharshh0007/CustomerSupportAgent
cd food-support-agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
copy env.template .env
# Edit .env and add your Google API key
# GOOGLE_API_KEY=your_google_api_key_here

# 4. Run the app
uvicorn app.main:app --reload

# 5. Access the App
Open http://localhost:8000 in your browser
```

---

## Deployment
**Live Demo URL:**
Not currently deployed. The app can be run locally using the setup steps above.

---

## Demo Video
**YouTube Link:**
`https://youtu.be/U6z7nzzFu0I`

---

## Features
- **Smart Order Tracking** - Automatically finds and displays order details when customers provide order IDs
- **Intelligent Refund Processing** - Calculates refund amounts based on order status and applies business rules
- **Semantic FAQ Search** - Uses RAG to find relevant answers even with different wording
- **Natural Language Understanding** - Handles conversational queries without rigid command structures
- **Real-time Chat Interface** - Clean, responsive web UI for seamless customer interaction

---

## Technical Architecture
The system works through a simple but effective pipeline:

- User sends message → FastAPI backend receives request
- Gemini agent analyzes the message and determines if a function call is needed
- If order ID detected → calls track_order() function
- If refund requested → calls process_refund() with business logic
- If general question → searches FAQ database using FAISS vector similarity
- Gemini formats the response combining function results with natural language
- Response sent back to frontend and displayed to user

The key innovation is the hybrid approach - using AI for understanding and formatting, but specific functions for accurate data retrieval and business logic.

---

## Testing
You can test the system with these sample queries:

```bash
# Order tracking
"Track my order FD123456789"

# Refund requests  
"I want a refund for FD111222333 because food was too spicy"

# FAQ queries
"How can I cancel my order?"
"What payment methods do you accept?"
```

---

## References
- [Google Gemini API](https://ai.google.dev/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Sentence Transformers](https://www.sbert.net/)

---

## License
This project is licensed under the MIT License.

---

## Acknowledgements
Thanks to Google for Gemini API, Facebook Research for FAISS, FastAPI team, and Sentence Transformers library. Vector similarity implementation in RAG engine was developed with ChatGPT support.