from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv
from app.gemini_agent import get_gemini_support_agent
from app.demo_agent import get_demo_support_agent

load_dotenv()

app = FastAPI(
    title="Food Support AI Agent",
    description="AI-powered customer support for food delivery app",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

try:
    support_agent = get_gemini_support_agent()
    demo_mode = False
    print("Gemini AI agent initialized successfully!")
except Exception as e:
    print(f"Failed to initialize Gemini agent: {e}")
    print("Switching to demo mode...")
    support_agent = get_demo_support_agent()
    demo_mode = True

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    success: bool
    response: str
    session_id: str
    function_called: Optional[str] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    message: str
    version: str

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main chat interface"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Food Support AI Agent</h1><p>Static files not found. Please check deployment.</p>")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessage):
    """Main chat endpoint for AI support"""
    try:
        if not chat_message.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        result = support_agent.chat(chat_message.message, chat_message.session_id)
        
        if demo_mode:
            result["demo_mode"] = True
        
        if result["success"]:
            return ChatResponse(
                success=True,
                response=result["response"],
                session_id=result["session_id"],
                function_called=result.get("function_called")
            )
        else:
            return ChatResponse(
                success=False,
                response=result.get("response", "An error occurred"),
                session_id=chat_message.session_id,
                error=result.get("error")
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/reset", response_model=Dict[str, Any])
async def reset_conversation(session_id: str = "default"):
    """Reset conversation history for a session"""
    try:
        result = support_agent.reset_conversation(session_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting conversation: {str(e)}")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for deployment"""
    return HealthResponse(
        status="healthy",
        message="Food Support AI Agent is running",
        version="1.0.0"
    )

@app.get("/api/orders/{order_id}")
async def get_order_info(order_id: str):
    """Get order information by ID (for testing)"""
    try:
        result = support_agent.tools.track_order(order_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching order: {str(e)}")

@app.get("/api/faq")
async def search_faq(query: str):
    """Search FAQs (for testing)"""
    try:
        result = support_agent.tools.search_faq(query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching FAQ: {str(e)}")

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint not found", "status_code": 404}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error", "status_code": 500}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )
