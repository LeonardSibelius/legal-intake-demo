"""
Intake Agent - Engine Room AI
The primary conversational agent for initial client intake
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class IntakeAgent(BaseAgent):
    """Primary intake agent - handles initial client conversations"""

    def __init__(self):
        super().__init__(
            name="IntakeAgent",
            description="Handles initial client intake conversations"
        )
        self.conversations: Dict[str, List] = {}

    def get_system_prompt(self) -> str:
        return """You are a friendly, professional legal intake assistant for a personal injury law firm.

YOUR MISSION:
Get the key facts about potential PI cases quickly and warmly. You're the first point of contact - make people feel heard while gathering what attorneys need.

CASE TYPES WE HANDLE:
- Auto accidents (cars, trucks, motorcycles, rideshare)
- Slip and fall / premises liability
- Medical malpractice
- Workplace injuries
- Product liability
- Wrongful death

CRITICAL INFO TO GATHER:
1. What happened? (type of incident)
2. When did it happen? (date is crucial for statute of limitations)
3. Were you injured? What injuries?
4. Have you seen a doctor / gotten treatment?
5. Who was at fault? (other driver, property owner, etc.)
6. Name and best contact number

CONVERSATION STYLE:
- Warm but efficient - people are hurting, don't waste their time
- Express genuine empathy for their situation
- Use simple language, no legal jargon
- Keep responses to 2-3 sentences
- Ask ONE question at a time

RED FLAGS TO WATCH FOR:
- "It happened a few years ago" - statute may be expired
- "I wasn't really hurt" - may not be a viable case
- "I already have a lawyer" - can't help
- "I was partially at fault" - note but don't dismiss

WHEN YOU HAVE ENOUGH INFO:
Summarize what you've learned and let them know:
"Thank you for sharing this with me. Based on what you've told me, an attorney will review your case and reach out within 24 hours. Is [their number] the best way to reach you?"

NEVER:
- Give legal advice
- Promise any outcome
- Discuss fees beyond "free consultation"
- Dismiss their case (leave that to attorneys)

Remember: Every call could be a $500K case. Treat them all with care."""

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a message in the intake conversation"""

        message = input_data.get('message', '')
        conversation_id = input_data.get('conversation_id', 'default')

        # Get or create conversation history
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        # Add user message
        self.conversations[conversation_id].append({
            "role": "user",
            "content": message
        })

        # Get response
        response = self.call_claude(self.conversations[conversation_id])

        # Add assistant response
        self.conversations[conversation_id].append({
            "role": "assistant",
            "content": response
        })

        # Extract any client info from conversation
        client_info = self._extract_client_info(self.conversations[conversation_id])

        return {
            'response': response,
            'conversation_id': conversation_id,
            'conversation': self.conversations[conversation_id],
            'client_info': client_info,
            'message_count': len(self.conversations[conversation_id])
        }

    def _extract_client_info(self, conversation: List[Dict]) -> Dict[str, Any]:
        """Extract client information from conversation (basic extraction)"""
        # In production, use Claude to extract structured data
        # For now, return empty dict - lead scorer will analyze full conversation
        return {}

    def get_conversation(self, conversation_id: str) -> List[Dict]:
        """Get conversation history"""
        return self.conversations.get(conversation_id, [])

    def reset_conversation(self, conversation_id: str):
        """Reset a conversation"""
        if conversation_id in self.conversations:
            self.conversations[conversation_id] = []


# Quick test
if __name__ == "__main__":
    agent = IntakeAgent()

    # Simulate a conversation
    messages = [
        "Hi, I was in a car accident",
        "Yesterday, I was rear-ended at a red light",
        "Yes, my neck and back are really sore. I went to urgent care this morning",
        "The other driver admitted it was their fault. They got a ticket",
        "My name is Sarah Johnson, 555-123-4567"
    ]

    for msg in messages:
        result = agent.process({
            'message': msg,
            'conversation_id': 'test_123'
        })
        print(f"USER: {msg}")
        print(f"AGENT: {result['response']}")
        print("-" * 50)
