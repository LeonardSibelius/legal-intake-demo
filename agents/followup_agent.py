"""
Follow-up Agent - Engine Room AI
Generates personalized follow-up messages based on lead status and conversation history
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from .base_agent import BaseAgent


class FollowupAgent(BaseAgent):
    """Generates and manages follow-up sequences for leads"""

    def __init__(self):
        super().__init__(
            name="FollowupAgent",
            description="Creates personalized follow-up messages and manages nurture sequences"
        )

    def get_system_prompt(self) -> str:
        return """You are a follow-up specialist for a personal injury law firm.
Your job is to write compelling, personalized follow-up messages that get responses.

TONE:
- Warm and caring, not salesy
- Reference specific details from their situation
- Create gentle urgency without being pushy
- Always offer value or next steps

MESSAGE TYPES:
1. IMMEDIATE (within hours) - For HOT leads, strike while iron is hot
2. 24H CHECK-IN - "Just checking if you have any questions"
3. 3-DAY NUDGE - Soft reminder with additional value
4. 7-DAY RE-ENGAGE - New angle, ask if situation changed
5. 14-DAY LAST CHANCE - Final outreach before archiving

RULES:
- Keep SMS under 160 characters when possible
- Emails should be 2-3 short paragraphs max
- Always include a clear call-to-action
- Never sound desperate or automated
- Personalize with their name and case details
- For injury cases, express genuine concern for their recovery

OUTPUT FORMAT:
Return JSON:
{
    "message_type": "sms" | "email",
    "subject": "<for email only>",
    "body": "<the message>",
    "send_time": "<recommended send time>",
    "follow_up_if_no_response": "<days until next follow-up>"
}"""

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a follow-up message"""

        lead_score = input_data.get('lead_score', {})
        conversation = input_data.get('conversation', [])
        client_info = input_data.get('client_info', {})
        follow_up_stage = input_data.get('follow_up_stage', 1)
        channel = input_data.get('channel', 'sms')  # sms or email

        # Determine follow-up type based on stage and score
        rating = lead_score.get('rating', 'WARM')

        context = self._build_context(lead_score, conversation, client_info, follow_up_stage)

        messages = [{
            "role": "user",
            "content": f"""Generate a {channel.upper()} follow-up message for this lead.

{context}

This is follow-up #{follow_up_stage}. Lead is rated {rating}.
Generate an appropriate {channel} message."""
        }]

        response = self.call_claude(messages)

        # Parse response
        try:
            import json
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            follow_up_data = json.loads(response.strip())
            self.log(f"Generated {channel} follow-up #{follow_up_stage}")
            return {'follow_up': follow_up_data}
        except:
            return {'follow_up': {'body': response, 'message_type': channel}}

    def _build_context(self, lead_score: dict, conversation: list, client_info: dict, stage: int) -> str:
        """Build context for follow-up generation"""
        parts = []

        if client_info:
            parts.append("CLIENT INFO:")
            for key, value in client_info.items():
                parts.append(f"  {key}: {value}")

        if lead_score:
            parts.append(f"\nLEAD SCORE: {lead_score.get('score', 'N/A')}")
            parts.append(f"CASE TYPE: {lead_score.get('case_type', 'N/A')}")
            parts.append(f"KEY FACTORS: {', '.join(lead_score.get('key_factors', []))}")

        if conversation:
            parts.append("\nORIGINAL CONVERSATION SUMMARY:")
            # Just include last few exchanges
            recent = conversation[-4:] if len(conversation) > 4 else conversation
            for msg in recent:
                parts.append(f"  {msg.get('role', '').upper()}: {msg.get('content', '')[:100]}...")

        parts.append(f"\nFOLLOW-UP STAGE: {stage}")

        return "\n".join(parts)

    def generate_sequence(self, lead_score: dict, client_info: dict) -> List[Dict]:
        """Generate a full follow-up sequence based on lead rating"""

        rating = lead_score.get('rating', 'WARM')

        if rating == 'HOT':
            # Aggressive follow-up for hot leads
            sequence = [
                {'stage': 1, 'delay_hours': 1, 'channel': 'sms'},
                {'stage': 2, 'delay_hours': 24, 'channel': 'email'},
                {'stage': 3, 'delay_hours': 72, 'channel': 'sms'},
                {'stage': 4, 'delay_hours': 168, 'channel': 'email'},
            ]
        elif rating == 'WARM':
            # Standard nurture for warm leads
            sequence = [
                {'stage': 1, 'delay_hours': 24, 'channel': 'email'},
                {'stage': 2, 'delay_hours': 72, 'channel': 'sms'},
                {'stage': 3, 'delay_hours': 168, 'channel': 'email'},
                {'stage': 4, 'delay_hours': 336, 'channel': 'email'},
            ]
        else:
            # Light touch for cold leads
            sequence = [
                {'stage': 1, 'delay_hours': 48, 'channel': 'email'},
                {'stage': 2, 'delay_hours': 168, 'channel': 'email'},
            ]

        return sequence


# Quick test
if __name__ == "__main__":
    agent = FollowupAgent()

    test_data = {
        'lead_score': {
            'score': 85,
            'rating': 'HOT',
            'case_type': 'Personal Injury - Auto Accident',
            'key_factors': ['Clear liability', 'Medical treatment', 'Recent incident']
        },
        'client_info': {
            'name': 'Maria Garcia',
            'phone': '555-987-6543'
        },
        'conversation': [
            {'role': 'user', 'content': 'I was hit by a truck yesterday at the intersection'},
            {'role': 'assistant', 'content': 'I\'m so sorry to hear that. Are you okay?'},
            {'role': 'user', 'content': 'I\'m in the hospital with a broken leg'}
        ],
        'follow_up_stage': 1,
        'channel': 'sms'
    }

    result = agent.process(test_data)
    print(result)
