import os
import json
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from app.tools import get_support_tools
from app.rag_engine import get_rag_engine
from dotenv import load_dotenv

load_dotenv()

class GeminiSupportAgent:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        self.tools = get_support_tools()
        self.rag_engine = get_rag_engine()
        self.conversation_history = []
        
        self.rag_engine.initialize()
    
    def _call_function(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call the appropriate function based on function name"""
        try:
            if function_name == "track_order":
                return self.tools.track_order(arguments["order_id"])
            elif function_name == "check_delivery_time":
                return self.tools.check_delivery_time(arguments["order_id"])
            elif function_name == "process_refund":
                return self.tools.process_refund(arguments["order_id"], arguments["reason"])
            elif function_name == "search_faq":
                return self.tools.search_faq(arguments["query"])
            elif function_name == "escalate_to_human":
                return self.tools.escalate_to_human(arguments["issue"])
            elif function_name == "get_restaurant_info":
                return self.tools.get_restaurant_info(arguments["restaurant_name"])
            else:
                return {"success": False, "message": f"Unknown function: {function_name}"}
        except Exception as e:
            return {"success": False, "message": f"Error calling function {function_name}: {str(e)}"}
    
    def _format_function_result(self, function_name: str, result: Dict[str, Any]) -> str:
        """Format function result for display"""
        if not result.get("success", False):
            return f"❌ {result.get('message', 'Unknown error')}"
        
        if function_name == "track_order":
            order_info = f"📦 **Order Summary - {result['order_id']}**\n\n"
            order_info += f"**Customer:** {result['customer_name']}\n"
            order_info += f"**Phone:** {result['customer_phone']}\n"
            order_info += f"**Restaurant:** {result['restaurant']}\n"
            order_info += f"**Status:** {result['status'].replace('_', ' ').title()}\n\n"
            
            order_info += f"**Items Ordered:**\n"
            for item in result['items']:
                order_info += f"• {item['name']} x{item['quantity']} - ${item['price']}\n"
            
            order_info += f"\n**Total Amount:** ${result['total_amount']}\n"
            order_info += f"**Delivery Address:** {result['delivery_address']}\n"
            order_info += f"**Order Time:** {result['order_time']}\n"
            order_info += f"**Estimated Delivery:** {result['estimated_delivery']}\n"
            
            if result.get('time_remaining'):
                order_info += f"**Time Remaining:** {result['time_remaining']}\n"
            
            if result.get('driver_name'):
                order_info += f"**Driver:** {result['driver_name']}\n"
                if result.get('driver_phone'):
                    order_info += f"**Driver Phone:** {result['driver_phone']}\n"
            
            if result.get('special_instructions'):
                order_info += f"**Special Instructions:** {result['special_instructions']}\n"
            
            if result.get('delivery_time'):
                order_info += f"**Delivered At:** {result['delivery_time']}\n"
            
            return order_info
        
        elif function_name == "check_delivery_time":
            return f"⏰ {result['message']}"
        
        elif function_name == "process_refund":
            return f"💰 {result['message']}"
        
        elif function_name == "search_faq":
            faq_text = f"📚 **FAQ Results:**\n\n"
            for faq in result['faqs']:
                faq_text += f"**Q:** {faq['question']}\n"
                faq_text += f"**A:** {faq['answer']}\n\n"
            return faq_text
        
        elif function_name == "escalate_to_human":
            return f"👨‍💼 {result['message']}"
        
        elif function_name == "get_restaurant_info":
            restaurant = result['restaurant']
            info_text = f"🍽️ **{restaurant['name']}**\n"
            info_text += f"Cuisine: {restaurant['cuisine']}\n"
            info_text += f"Rating: {restaurant['rating']}/5\n"
            info_text += f"Delivery time: {restaurant['delivery_time']}\n"
            info_text += f"Delivery fee: ${restaurant['delivery_fee']}\n"
            return info_text
        
        return result.get('message', 'Function executed successfully')
    
    def _extract_function_call(self, user_message: str, response_text: str) -> Optional[Dict[str, Any]]:
        """Extract function call from user message and Gemini response"""
        import re
        
        # Check user message for order IDs first
        order_match = re.search(r'FD\d{9}', user_message)
        if order_match:
            order_id = order_match.group()
            
            if (len(user_message.strip()) <= 15 or  
                any(word in user_message.lower() for word in ["yes", "please", "ok", "okay", "sure", "track", "status", "where", "order", "delivery", "show", "details", "summary"])):
                return {
                    "function_name": "track_order",
                    "arguments": {"order_id": order_id}
                }
            
            if any(word in user_message.lower() for word in ["refund", "cancel", "return", "money back"]):
                return {
                    "function_name": "process_refund",
                    "arguments": {"order_id": order_id, "reason": "Customer request"}
                }
        
        if any(word in user_message.lower() for word in ["how", "what", "when", "where", "can i", "do you", "payment", "cancel", "delivery", "time", "fee"]):
            return {
                "function_name": "search_faq",
                "arguments": {"query": user_message}
            }
        
        if any(restaurant in user_message.lower() for restaurant in ["mario", "sushi", "burger", "thai", "subway"]):
            if "mario" in user_message.lower():
                restaurant_name = "Mario's Pizza"
            elif "sushi" in user_message.lower():
                restaurant_name = "Sushi Palace"
            elif "burger" in user_message.lower():
                restaurant_name = "Burger King"
            elif "thai" in user_message.lower():
                restaurant_name = "Thai Garden"
            elif "subway" in user_message.lower():
                restaurant_name = "Subway"
            else:
                restaurant_name = "Mario's Pizza"  # default
            
            return {
                "function_name": "get_restaurant_info",
                "arguments": {"restaurant_name": restaurant_name}
            }
        
        if any(word in user_message.lower() for word in ["manager", "supervisor", "escalate", "complaint", "serious", "urgent"]):
            return {
                "function_name": "escalate_to_human",
                "arguments": {"issue": user_message}
            }
        
        return None
    
    def chat(self, user_message: str, session_id: str = "default") -> Dict[str, Any]:
        """Process user message and return AI response"""
        try:
            # Add user message to conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            
            # Prepare context for Gemini
            context = f"""You are a helpful customer support agent for a food delivery app. 

IMPORTANT: When a user provides an order ID (like FD123456789), you should suggest tracking that order. When they ask questions about policies, suggest searching FAQs.

Available functions you can suggest:
- track_order(order_id): Track order status - use when user mentions order ID
- process_refund(order_id, reason): Process refund requests
- search_faq(query): Search FAQs - use for policy questions
- get_restaurant_info(restaurant_name): Get restaurant details
- escalate_to_human(issue): Escalate complex issues

Sample order IDs: FD123456789, FD987654321, FD555666777, FD111222333
Available restaurants: Mario's Pizza, Sushi Palace, Burger King, Thai Garden, Subway

User message: "{user_message}"

Instructions:
1. If user mentions an order ID, suggest tracking it
2. If user asks about policies/rules, suggest FAQ search
3. Be friendly and helpful
4. Always suggest the appropriate function when relevant

Previous conversation:
{self.conversation_history[-4:] if len(self.conversation_history) > 1 else []}
            """
            
            response = self.model.generate_content(context)
            response_text = response.text
            
            function_call = self._extract_function_call(user_message, response_text)
            
            if function_call:
                function_result = self._call_function(
                    function_call["function_name"], 
                    function_call["arguments"]
                )
                
                formatted_result = self._format_function_result(
                    function_call["function_name"], 
                    function_result
                )
                
                final_context = f"""Based on the function call result, provide a helpful response to the customer.
                
                Function called: {function_call["function_name"]}
                Function result: {json.dumps(function_result)}
                Formatted result: {formatted_result}
                
                Original user message: {user_message}
                
                Provide a friendly, helpful response incorporating the function result."""
                
                final_response = self.model.generate_content(final_context)
                full_response = f"{formatted_result}\n\n{final_response.text}"
                
            else:
                full_response = response_text
            
            # Add AI response to conversation history
            self.conversation_history.append({"role": "assistant", "content": full_response})
            
            return {
                "success": True,
                "response": full_response,
                "session_id": session_id,
                "function_called": function_call["function_name"] if function_call else None,
                "ai_model": "gemini-2.0-flash-exp"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "I'm sorry, I encountered an error. Please try again or contact support.",
                "ai_model": "gemini-2.0-flash-exp"
            }
    
    def reset_conversation(self, session_id: str = "default"):
        """Reset conversation history for a session"""
        self.conversation_history = []
        return {"success": True, "message": "Conversation reset"}

gemini_support_agent = GeminiSupportAgent()

def get_gemini_support_agent() -> GeminiSupportAgent:
    """Get the global Gemini support agent instance"""
    return gemini_support_agent
