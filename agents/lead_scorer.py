"""
Lead Scoring Agent - Engine Room AI
Analyzes intake conversations and scores leads as Hot/Warm/Cold
"""

from typing import Dict, Any
from .base_agent import BaseAgent


class LeadScoringAgent(BaseAgent):
    """Scores leads based on intake conversation data"""

    def __init__(self):
        super().__init__(
            name="LeadScorer",
            description="Analyzes intake data and scores leads for prioritization"
        )

    def get_system_prompt(self) -> str:
        return """You are a lead scoring specialist for a personal injury law firm.
Your job is to analyze intake conversations and score leads.

SCORING CRITERIA:

🔥 HOT (Score 80-100) - High-value, urgent cases:
- Serious injuries (hospitalization, surgery, ongoing treatment)
- Clear liability (rear-ended, slip on wet floor with no sign, etc.)
- Recent incident (within last 30 days)
- Has medical documentation or treatment
- Commercial vehicle/trucking accidents
- Medical malpractice with damages
- Wrongful death cases

⚡ WARM (Score 40-79) - Good potential, needs nurturing:
- Moderate injuries (soft tissue, whiplash)
- Liability is probable but not certain
- Incident 30-90 days ago
- Seeking medical treatment but not yet documented
- Property damage significant but injuries unclear
- Employment disputes with clear damages

❄️ COLD (Score 0-39) - Low priority or likely decline:
- Minor or no injuries
- Incident over 90 days ago (statute concerns)
- Unclear liability (multi-car, shared fault)
- "Fishing" for information only
- Already has attorney
- Out of jurisdiction
- Case type firm doesn't handle

OUTPUT FORMAT:
Return a JSON object with:
{
    "score": <0-100>,
    "rating": "HOT" | "WARM" | "COLD",
    "case_type": "<type of case>",
    "key_factors": ["factor1", "factor2", ...],
    "red_flags": ["flag1", "flag2", ...] or [],
    "recommended_action": "<what to do next>",
    "urgency": "immediate" | "24h" | "48h" | "weekly" | "archive",
    "estimated_value": "high" | "medium" | "low" | "unknown",
    "summary": "<1-2 sentence summary for attorney>"
}

Be decisive. Attorneys don't have time for "maybe" - give them a clear recommendation."""

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score a lead based on conversation data"""

        conversation = input_data.get('conversation', [])
        client_info = input_data.get('client_info', {})

        # Build context for scoring
        context = self._build_context(conversation, client_info)

        messages = [{
            "role": "user",
            "content": f"""Score this lead based on the intake conversation:

{context}

Analyze and return the scoring JSON."""
        }]

        response = self.call_claude(messages)

        # Parse the response
        try:
            import json
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            score_data = json.loads(response.strip())
            self.log(f"Scored lead: {score_data.get('rating')} ({score_data.get('score')})")
            return {'lead_score': score_data}
        except json.JSONDecodeError:
            self.log(f"Failed to parse score response")
            return {'lead_score': {'error': 'Failed to parse', 'raw': response}}

    def _build_context(self, conversation: list, client_info: dict) -> str:
        """Build context string from conversation and client info"""
        parts = []

        if client_info:
            parts.append("CLIENT INFO:")
            for key, value in client_info.items():
                parts.append(f"  {key}: {value}")
            parts.append("")

        if conversation:
            parts.append("CONVERSATION:")
            for msg in conversation:
                role = msg.get('role', 'unknown').upper()
                content = msg.get('content', '')
                parts.append(f"  {role}: {content}")

        return "\n".join(parts)


# Quick test
if __name__ == "__main__":
    agent = LeadScoringAgent()

    test_data = {
        'conversation': [
            {'role': 'user', 'content': 'I was rear-ended at a stoplight yesterday'},
            {'role': 'assistant', 'content': 'I\'m sorry to hear that. Were you injured?'},
            {'role': 'user', 'content': 'Yes, my neck hurts badly. I went to the ER and they said I have whiplash. I\'m in a lot of pain.'},
            {'role': 'assistant', 'content': 'That sounds serious. Did the other driver admit fault?'},
            {'role': 'user', 'content': 'Yes, they got a ticket. Their insurance already called me.'}
        ],
        'client_info': {
            'name': 'John Smith',
            'phone': '555-123-4567',
            'incident_date': '2026-01-30'
        }
    }

    result = agent.process(test_data)
    print(result)
