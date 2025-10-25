import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import random
from app.rag_engine import get_rag_engine

class SupportTools:
    def __init__(self):
        self.order_database = self._load_order_database()
        self.restaurant_data = self._load_restaurant_data()
        self.refund_policies = self._load_refund_policies()
        self.rag_engine = get_rag_engine()
        
    def _load_order_database(self) -> List[Dict[str, Any]]:
        """Load order database from JSON file"""
        try:
            with open("data/order_database.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Order database not found")
            return []
    
    def _load_restaurant_data(self) -> List[Dict[str, Any]]:
        """Load restaurant data from JSON file"""
        try:
            with open("data/restaurant_data.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Restaurant data not found")
            return []
    
    def _load_refund_policies(self) -> Dict[str, Any]:
        """Load refund policies from JSON file"""
        try:
            with open("data/refund_policies.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Refund policies not found")
            return {}
    
    def track_order(self, order_id: str) -> Dict[str, Any]:
        """Track an order by order ID with comprehensive summary"""
        order = next((o for o in self.order_database if o["order_id"] == order_id), None)
        
        if not order:
            return {
                "success": False,
                "message": f"Order {order_id} not found. Please check your order ID and try again.",
                "order_id": order_id
            }
        
        time_remaining = None
        if order["status"] in ["confirmed", "preparing", "out_for_delivery"]:
            estimated_delivery = datetime.fromisoformat(order["estimated_delivery"].replace('Z', '+00:00'))
            now = datetime.now(estimated_delivery.tzinfo)
            if estimated_delivery > now:
                remaining_minutes = int((estimated_delivery - now).total_seconds() / 60)
                time_remaining = f"{remaining_minutes} minutes"
        
        order_summary = {
            "success": True,
            "order_id": order_id,
            "customer_name": order["customer_name"],
            "customer_phone": order["customer_phone"],
            "restaurant": order["restaurant"],
            "items": order["items"],
            "total_amount": order["total_amount"],
            "delivery_address": order["delivery_address"],
            "order_time": order["order_time"],
            "estimated_delivery": order["estimated_delivery"],
            "status": order["status"],
            "time_remaining": time_remaining,
            "driver_name": order.get("driver_name"),
            "driver_phone": order.get("driver_phone"),
            "special_instructions": order.get("special_instructions"),
            "delivery_time": order.get("delivery_time")
        }
        
        return order_summary
    
    def check_delivery_time(self, order_id: str) -> Dict[str, Any]:
        """Check delivery time for an order"""
        order = next((o for o in self.order_database if o["order_id"] == order_id), None)
        
        if not order:
            return {
                "success": False,
                "message": f"Order {order_id} not found.",
                "order_id": order_id
            }
        
        estimated_delivery = datetime.fromisoformat(order["estimated_delivery"].replace('Z', '+00:00'))
        now = datetime.now(estimated_delivery.tzinfo)
        
        if order["status"] == "delivered":
            delivery_time = datetime.fromisoformat(order.get("delivery_time", order["estimated_delivery"]).replace('Z', '+00:00'))
            return {
                "success": True,
                "order_id": order_id,
                "status": "delivered",
                "delivered_at": order.get("delivery_time"),
                "message": "Your order has been delivered!"
            }
        elif estimated_delivery > now:
            remaining_minutes = int((estimated_delivery - now).total_seconds() / 60)
            return {
                "success": True,
                "order_id": order_id,
                "status": order["status"],
                "estimated_delivery": order["estimated_delivery"],
                "time_remaining": f"{remaining_minutes} minutes",
                "message": f"Your order will be delivered in approximately {remaining_minutes} minutes."
            }
        else:
            return {
                "success": True,
                "order_id": order_id,
                "status": order["status"],
                "message": "Your order is running late. Please contact support for assistance."
            }
    
    def process_refund(self, order_id: str, reason: str) -> Dict[str, Any]:
        """Process a refund request for an order"""
        order = next((o for o in self.order_database if o["order_id"] == order_id), None)
        
        if not order:
            return {
                "success": False,
                "message": f"Order {order_id} not found.",
                "order_id": order_id
            }
        
        # Check if order is eligible for refund
        order_time = datetime.fromisoformat(order["order_time"].replace('Z', '+00:00'))
        now = datetime.now(order_time.tzinfo)
        time_since_order = (now - order_time).total_seconds() / 3600  # hours
        
        refund_amount = 0
        refund_type = "none"
        
        if time_since_order < 0.083:  # Less than 5 minutes
            refund_amount = order["total_amount"]
            refund_type = "full"
        elif order["status"] == "delivered" and time_since_order < 2:  # Delivered within 2 hours
            if "wrong" in reason.lower() or "damaged" in reason.lower():
                refund_amount = order["total_amount"]
                refund_type = "full"
            elif "late" in reason.lower() or "cold" in reason.lower():
                refund_amount = order["total_amount"] * 0.2  # 20% refund
                refund_type = "partial"
        elif order["status"] in ["confirmed", "preparing"]:
            refund_amount = order["total_amount"] * 0.5  # 50% refund
            refund_type = "partial"
        
        if refund_amount > 0:
            return {
                "success": True,
                "order_id": order_id,
                "refund_amount": round(refund_amount, 2),
                "refund_type": refund_type,
                "reason": reason,
                "processing_time": "3-5 business days",
                "message": f"Refund approved for ${refund_amount:.2f}. The amount will be credited to your original payment method within 3-5 business days."
            }
        else:
            return {
                "success": False,
                "order_id": order_id,
                "reason": reason,
                "message": "This order is not eligible for a refund based on our policy. Please contact support for further assistance."
            }
    
    def search_faq(self, query: str) -> Dict[str, Any]:
        """Search FAQs using RAG"""
        relevant_faqs = self.rag_engine.get_relevant_faqs(query, threshold=0.3)
        
        if not relevant_faqs:
            return {
                "success": False,
                "query": query,
                "message": "No relevant FAQs found. Please try rephrasing your question or contact support for assistance."
            }
        
        return {
            "success": True,
            "query": query,
            "faqs": relevant_faqs,
            "message": f"Found {len(relevant_faqs)} relevant FAQ(s) for your query."
        }
    
    def escalate_to_human(self, issue: str) -> Dict[str, Any]:
        """Escalate complex issues to human support"""
        # Generate a support ticket ID
        ticket_id = f"TICKET-{random.randint(100000, 999999)}"
        
        return {
            "success": True,
            "ticket_id": ticket_id,
            "issue": issue,
            "message": f"Your issue has been escalated to our human support team. Ticket ID: {ticket_id}. A support agent will contact you within 5 minutes.",
            "estimated_response_time": "5 minutes",
            "contact_methods": [
                "In-app chat",
                "Phone: 1-800-FOOD-HELP",
                "Email: support@fooddelivery.com"
            ]
        }
    
    def get_restaurant_info(self, restaurant_name: str) -> Dict[str, Any]:
        """Get information about a restaurant"""
        restaurant = next((r for r in self.restaurant_data if r["name"].lower() == restaurant_name.lower()), None)
        
        if not restaurant:
            return {
                "success": False,
                "message": f"Restaurant '{restaurant_name}' not found in our database."
            }
        
        return {
            "success": True,
            "restaurant": restaurant,
            "message": f"Here's the information for {restaurant['name']}."
        }
    
    def get_order_summary(self, order_id: str) -> Dict[str, Any]:
        """Get comprehensive order summary for RAG retrieval"""
        order = next((o for o in self.order_database if o["order_id"] == order_id), None)
        
        if not order:
            return {
                "success": False,
                "message": f"Order {order_id} not found.",
                "order_id": order_id
            }
        
        # Create a comprehensive summary for RAG
        items_text = ", ".join([f"{item['name']} (x{item['quantity']})" for item in order['items']])
        
        summary = f"""
        Order ID: {order['order_id']}
        Customer: {order['customer_name']}
        Restaurant: {order['restaurant']}
        Items: {items_text}
        Total: ${order['total_amount']}
        Status: {order['status']}
        Delivery Address: {order['delivery_address']}
        Order Time: {order['order_time']}
        Estimated Delivery: {order['estimated_delivery']}
        """
        
        if order.get('driver_name'):
            summary += f"Driver: {order['driver_name']}"
        
        return {
            "success": True,
            "order_id": order_id,
            "summary": summary.strip(),
            "order_data": order
        }

support_tools = SupportTools()

def get_support_tools() -> SupportTools:
    """Get the global support tools instance"""
    return support_tools
