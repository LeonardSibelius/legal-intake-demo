"""
Research Agent - Engine Room AI
Harvey-lite: Legal research, statute lookups, jurisdiction rules, case precedents
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class ResearchAgent(BaseAgent):
    """Legal research assistant - provides case-relevant legal information"""

    def __init__(self):
        super().__init__(
            name="ResearchAgent",
            description="Provides legal research, statute information, and case precedents"
        )
        self.max_tokens = 2000  # Research needs more output

    def get_system_prompt(self) -> str:
        return """You are a legal research assistant for a personal injury law firm.
Your job is to provide relevant legal information to help attorneys evaluate cases.

IMPORTANT DISCLAIMERS:
- You provide RESEARCH, not legal advice
- Always note that laws change and verification is needed
- Flag any uncertainty in your research
- Recommend consultation with the attorney for final decisions

RESEARCH CAPABILITIES:

1. STATUTE OF LIMITATIONS by state:
   - Personal injury: typically 2-3 years
   - Medical malpractice: varies widely (1-6 years)
   - Product liability: varies by state
   - Wrongful death: typically 2 years
   - Discovery rule exceptions

2. JURISDICTION ANALYSIS:
   - Where can the case be filed?
   - Federal vs state court considerations
   - Venue rules for multi-state incidents

3. LIABILITY FRAMEWORKS:
   - Negligence standards
   - Comparative vs contributory negligence states
   - Strict liability scenarios
   - Vicarious liability (employer responsibility)

4. DAMAGES OVERVIEW:
   - Economic damages (medical, lost wages)
   - Non-economic damages (pain and suffering)
   - Punitive damages availability
   - Damage caps by state

5. CASE TYPE SPECIFIC:
   - Auto: insurance requirements, no-fault states
   - Trucking: FMCSA regulations, hours of service
   - Medical mal: expert requirements, caps
   - Premises: duty of care standards
   - Product: manufacturing vs design defects

OUTPUT FORMAT:
{
    "research_summary": "<brief overview>",
    "statute_of_limitations": {
        "state": "<state>",
        "deadline": "<date or timeframe>",
        "exceptions": ["<any exceptions>"],
        "urgency": "critical" | "standard" | "flexible"
    },
    "liability_analysis": {
        "framework": "<negligence type>",
        "key_elements": ["<elements to prove>"],
        "potential_defendants": ["<who can be sued>"],
        "challenges": ["<potential issues>"]
    },
    "damages_potential": {
        "economic": "<assessment>",
        "non_economic": "<assessment>",
        "punitive": "<availability>",
        "caps": "<any caps that apply>"
    },
    "key_precedents": [
        {"case": "<case name>", "relevance": "<why relevant>"}
    ],
    "recommended_actions": ["<next steps>"],
    "red_flags": ["<concerns to address>"],
    "attorney_notes": "<summary for reviewing attorney>"
}

Be thorough but concise. Attorneys are busy."""

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct legal research for a case"""

        lead_score = input_data.get('lead_score', {})
        conversation = input_data.get('conversation', [])
        client_info = input_data.get('client_info', {})
        state = input_data.get('state', 'Nevada')  # Default to Nevada
        research_type = input_data.get('research_type', 'full')

        case_type = lead_score.get('case_type', 'Personal Injury')
        key_factors = lead_score.get('key_factors', [])

        # Build research request
        context = self._build_case_context(case_type, key_factors, conversation, state)

        if research_type == 'statute_only':
            return self._research_statute(case_type, state)
        elif research_type == 'liability_only':
            return self._research_liability(case_type, context)
        else:
            return self._full_research(case_type, context, state)

    def _build_case_context(self, case_type: str, key_factors: list, conversation: list, state: str) -> str:
        """Build context for research request"""
        parts = [
            f"CASE TYPE: {case_type}",
            f"STATE: {state}",
            f"KEY FACTORS: {', '.join(key_factors)}"
        ]

        if conversation:
            parts.append("\nRELEVANT CASE FACTS FROM INTAKE:")
            for msg in conversation:
                if msg.get('role') == 'user':
                    parts.append(f"  - {msg.get('content', '')[:200]}")

        return "\n".join(parts)

    def _full_research(self, case_type: str, context: str, state: str) -> Dict[str, Any]:
        """Conduct full legal research"""

        messages = [{
            "role": "user",
            "content": f"""Conduct legal research for this case:

{context}

Provide comprehensive research including:
1. Statute of limitations for {state}
2. Liability framework and elements to prove
3. Damages potential and any caps
4. Relevant case precedents or statutes
5. Recommended next steps
6. Any red flags or concerns

Return as detailed JSON."""
        }]

        response = self.call_claude(messages)

        try:
            import json
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            research = json.loads(response.strip())
            self.log(f"Completed full research for {case_type} in {state}")
            return {'research': research}
        except:
            return {'research': {'research_summary': response}}

    def _research_statute(self, case_type: str, state: str) -> Dict[str, Any]:
        """Quick statute of limitations lookup"""

        # Common statutes (would be database lookup in production)
        statutes = {
            'Nevada': {
                'personal_injury': '2 years',
                'medical_malpractice': '3 years from injury or 1 year from discovery',
                'wrongful_death': '2 years',
                'product_liability': '2 years'
            },
            'California': {
                'personal_injury': '2 years',
                'medical_malpractice': '3 years from injury or 1 year from discovery',
                'wrongful_death': '2 years',
                'product_liability': '2 years'
            },
            'Texas': {
                'personal_injury': '2 years',
                'medical_malpractice': '2 years',
                'wrongful_death': '2 years',
                'product_liability': '2 years'
            }
        }

        state_statutes = statutes.get(state, statutes['Nevada'])

        # Determine which statute applies
        if 'medical' in case_type.lower() or 'malpractice' in case_type.lower():
            sol = state_statutes['medical_malpractice']
            sol_type = 'medical_malpractice'
        elif 'death' in case_type.lower():
            sol = state_statutes['wrongful_death']
            sol_type = 'wrongful_death'
        elif 'product' in case_type.lower():
            sol = state_statutes['product_liability']
            sol_type = 'product_liability'
        else:
            sol = state_statutes['personal_injury']
            sol_type = 'personal_injury'

        return {
            'statute_of_limitations': {
                'state': state,
                'case_type': sol_type,
                'deadline': sol,
                'note': 'Verify current law - statutes may have changed',
                'discovery_rule': 'May apply if injury was not immediately apparent'
            }
        }

    def _research_liability(self, case_type: str, context: str) -> Dict[str, Any]:
        """Research liability framework"""

        messages = [{
            "role": "user",
            "content": f"""Analyze liability for this case:

{context}

Provide:
1. Applicable liability framework (negligence, strict liability, etc.)
2. Elements plaintiff must prove
3. Potential defendants
4. Likely defenses
5. Comparative fault considerations

Return as JSON with liability_analysis object."""
        }]

        response = self.call_claude(messages)

        try:
            import json
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response.strip())
        except:
            return {'liability_analysis': {'summary': response}}

    def get_quick_facts(self, state: str, case_type: str) -> Dict[str, Any]:
        """Get quick reference facts for a case type in a state"""

        # Negligence standards by state
        comparative_fault_states = [
            'California', 'New York', 'Florida', 'Texas', 'Nevada', 'Arizona',
            'Colorado', 'Michigan', 'Ohio', 'Pennsylvania'
        ]

        contributory_states = ['Alabama', 'Maryland', 'North Carolina', 'Virginia', 'DC']

        no_fault_auto_states = [
            'Florida', 'Michigan', 'New Jersey', 'New York', 'Pennsylvania',
            'Hawaii', 'Kansas', 'Kentucky', 'Massachusetts', 'Minnesota',
            'North Dakota', 'Utah'
        ]

        return {
            'state': state,
            'negligence_standard': 'contributory' if state in contributory_states else 'comparative',
            'no_fault_auto': state in no_fault_auto_states,
            'note': 'Quick reference only - verify current law'
        }


# Quick test
if __name__ == "__main__":
    agent = ResearchAgent()

    test_data = {
        'lead_score': {
            'rating': 'HOT',
            'case_type': 'Personal Injury - Commercial Trucking Accident',
            'key_factors': ['Commercial vehicle', 'Serious injuries', 'Clear liability']
        },
        'conversation': [
            {'role': 'user', 'content': 'I was hit by an Amazon delivery truck that ran a red light'},
            {'role': 'user', 'content': 'I have a broken leg and fractured ribs, been in hospital for 3 days'}
        ],
        'state': 'Nevada',
        'research_type': 'full'
    }

    result = agent.process(test_data)
    print(result)
