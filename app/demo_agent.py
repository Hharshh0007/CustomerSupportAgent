import os
import json
from typing import Dict, List, Any, Optional
from app.tools import get_support_tools
from app.rag_engine import get_rag_engine
from dotenv import load_dotenv

load_dotenv()

class DemoSupportAgent:
    def __init__(self):
        self.tools = get_support_tools()
        self.rag_engine = get_rag_engine()
        self.conversation_history = []
        
        self.rag_engine.initialize()
    
    def _simulate_function_call(self, user_message: str) -> Dict[str, Any]:
        """Simulate function calls based on user message patterns"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ["track", "status", "order"]):
            if "fd123456789" in message_lower:
                return {
                    "function_name": "track_order",
                    "result": self.tools.track_order("FD123456789")
                }
            elif "fd987654321" in message_lower:
                return {
                    "function_name": "track_order", 
                    "result": self.tools.track_order("FD987654321")
                }
        
        if any(word in message_lower for word in ["cancel", "refund", "payment", "delivery", "how", "what", "when"]):
            return {
                "function_name": "search_faq",
                "result": self.tools.search_faq(user_message)
            }
        
        if "refund" in message_lower and any(order_id in message_lower for order_id in ["fd123456789", "fd987654321"]):
            order_id = "FD123456789" if "fd123456789" in message_lower else "FD987654321"
            return {
                "function_name": "process_refund",
                "result": self.tools.process_refund(order_id, "Food was cold")
            }
        
        if any(restaurant in message_lower for restaurant in ["mario", "sushi", "burger", "thai"]):
            restaurant_name = "Mario's Pizza" if "mario" in message_lower else "Sushi Palace"
            return {
                "function_name": "get_restaurant_info",
                "result": self.tools.get_restaurant_info(restaurant_name)
            }
        
        # Default FAQ search
        return {
            "function_name": "search_faq",
            "result": self.tools.search_faq(user_message)
        }
    
    def _format_demo_response(self, function_name: str, result: Dict[str, Any], user_message: str) -> str:
        """Format a demo response"""
        if not result.get("success", False):
            return f"❌ {result.get('message', 'Unknown error')}"
        
        if function_name == "track_order":
            order_info = f"📦 **Order {result['order_id']}**\n"
            order_info += f"Status: {result['status'].replace('_', ' ').title()}\n"
            order_info += f"Restaurant: {result['restaurant']}\n"
            order_info += f"Total: ${result['total_amount']}\n"
            if result.get('time_remaining'):
                order_info += f"Time remaining: {result['time_remaining']}\n"
            if result.get('driver_name'):
                order_info += f"Driver: {result['driver_name']}\n"
            return order_info + "\n\nI can help you with any questions about your order!"
        
        elif function_name == "search_faq":
            faq_text = f"📚 **Here's what I found:**\n\n"
            for faq in result['faqs']:
                faq_text += f"**Q:** {faq['question']}\n"
                faq_text += f"**A:** {faq['answer']}\n\n"
            return faq_text + "Is there anything else I can help you with?"
        
        elif function_name == "process_refund":
            return f"💰 {result['message']}\n\nI've processed your refund request. Is there anything else I can assist you with?"
        
        elif function_name == "get_restaurant_info":
            restaurant = result['restaurant']
            info_text = f"🍽️ **{restaurant['name']}**\n"
            info_text += f"Cuisine: {restaurant['cuisine']}\n"
            info_text += f"Rating: {restaurant['rating']}/5\n"
            info_text += f"Delivery time: {restaurant['delivery_time']}\n"
            info_text += f"Delivery fee: ${restaurant['delivery_fee']}\n"
            return info_text + "\nWould you like to know more about this restaurant?"
        
        return result.get('message', 'Function executed successfully')
    
    def chat(self, user_message: str, session_id: str = "default") -> Dict[str, Any]:
        """Process user message and return demo response"""
        try:
            self.conversation_history.append({"role": "user", "content": user_message})
            
            function_result = self._simulate_function_call(user_message)
            
            response = self._format_demo_response(
                function_result["function_name"], 
                function_result["result"], 
                user_message
            )
            
            # Add AI response to conversation history
            self.conversation_history.append({"role": "assistant", "content": response})
            
            return {
                "success": True,
                "response": response,
                "session_id": session_id,
                "function_called": function_result["function_name"],
                "demo_mode": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "I'm sorry, I encountered an error. Please try again or contact support.",
                "demo_mode": True
            }
    
    def reset_conversation(self, session_id: str = "default"):
        """Reset conversation history for a session"""
        self.conversation_history = []
        return {"success": True, "message": "Conversation reset", "demo_mode": True}

demo_support_agent = DemoSupportAgent()

def get_demo_support_agent() -> DemoSupportAgent:
    """Get the global demo support agent instance"""
    return demo_support_agent
