# Food Support AI Agent - Test Queries


### 1. Basic Order Tracking
- "Track my order FD123456789"
- "What's the status of order FD987654321?"
- "Is my order FD555666777 delivered yet?"

### 2. Delivery Time Queries
- "When will my order FD123456789 arrive?"
- "How long until delivery for FD987654321?"
- "Check delivery time for FD111222333"

### 3. FAQ Search (RAG Demo)
- "How can I cancel my order?"
- "What payment methods do you accept?"
- "How do I get a refund?"
- "My order is late, what should I do?"
- "How do I contact customer support?"
- "Do you offer discounts?"

### 4. Refund Requests
- "I want a refund for order FD123456789 because the food was cold"
- "Process refund for FD987654321, wrong order received"
- "Refund order FD555666777, delivery was 2 hours late"

### 5. Restaurant Information
- "Tell me about Mario's Pizza"
- "What's the rating for Sushi Palace?"
- "Info about Burger King"

### 6. Complex Scenarios (Escalation)
- "I've been waiting 3 hours for my order and the driver won't answer calls"
- "The food made me sick and I need immediate assistance"
- "I want to speak to a manager about a serious complaint"

### 7. Multi-turn Conversations
- "Track order FD123456789" → "When will it arrive?" → "Can I cancel it?"
- "How do I get a refund?" → "I want to refund order FD987654321" → "What's the reason?"

### 8. Edge Cases
- "Track order INVALID123" (non-existent order)
- "Refund order FD123456789 because I don't like the taste" (weak reason)
- "What's the weather like?" (off-topic)