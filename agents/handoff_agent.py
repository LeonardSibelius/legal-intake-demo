"""
Handoff Agent - Engine Room AI
Detects when to escalate to humans, routes to appropriate attorney
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .base_agent import BaseAgent


class HandoffAgent(BaseAgent):
    """Manages escalations and routes cases to appropriate attorneys"""

    def __init__(self):
        super().__init__(
            name="HandoffAgent",
            description="Detects escalation triggers and routes to appropriate human staff"
        )

        # Attorney roster (would be database in production)
        self.attorneys = {
            'senior_partner': {
                'name': 'Senior Partner',
                'specialties': ['commercial_trucking', 'wrongful_death', 'catastrophic_injury'],
                'min_case_value': 'high',
                'availability': 'by_appointment'
            },
            'pi_associate_1': {
                'name': 'PI Associate',
                'specialties': ['auto_accident', 'slip_fall', 'general_pi'],
                'min_case_value': 'any',
                'availability': 'standard_hours'
            },
            'intake_coordinator': {
                'name': 'Intake Coordinator',
                'specialties': ['all'],
                'role': 'initial_screening',
                'availability': 'business_hours'
            }
        }

        # Escalation triggers
        self.immediate_escalation_triggers = [
            'currently in danger',
            'being threatened',
            'suicidal',
            'emergency',
            'arrested',
            'in custody',
            'child in danger',
            'domestic violence',
            'active crime'
        ]

    def get_system_prompt(self) -> str:
        return """You are an escalation and routing specialist for a personal injury law firm.
Your job is to detect when AI should hand off to humans and route to the right person.

IMMEDIATE HUMAN ESCALATION (drop everything):
- Client mentions being in danger
- Domestic violence situations
- Suicidal ideation
- Active emergencies (call 911 first)
- Arrested or in police custody
- Child safety concerns

ATTORNEY ESCALATION (priority routing):
- High-value commercial cases (trucking, airline, cruise)
- Wrongful death cases
- Catastrophic injuries (paralysis, brain injury, amputation)
- Medical malpractice
- Cases involving minors
- Cases with media attention potential
- Government entity defendants
- Complex multi-party cases

STANDARD ROUTING:
- Typical auto accidents → PI Associate
- Slip and fall → PI Associate
- General inquiries → Intake Coordinator
- Cases we don't handle → Polite referral

ROUTING CONSIDERATIONS:
- Attorney specialties and caseload
- Case complexity and value
- Urgency (statute of limitations)
- Client preferences (Spanish-speaking attorney, etc.)
- Time of day (who's available)

OUTPUT FORMAT:
{
    "escalation_needed": true | false,
    "escalation_type": "immediate" | "priority" | "standard" | "none",
    "reason": "<why escalation>",
    "route_to": {
        "role": "<attorney/coordinator role>",
        "name": "<specific person if applicable>",
        "reason": "<why this person>"
    },
    "client_message": "<what to tell the client>",
    "internal_notes": "<notes for receiving staff>",
    "urgency": "immediate" | "same_day" | "24_hours" | "standard"
}"""

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze conversation and determine routing"""

        conversation = input_data.get('conversation', [])
        lead_score = input_data.get('lead_score', {})
        client_info = input_data.get('client_info', {})
        current_message = input_data.get('current_message', '')

        # Check for immediate escalation triggers first
        immediate_check = self._check_immediate_escalation(current_message, conversation)
        if immediate_check['escalation_needed']:
            return immediate_check

        # Analyze for priority routing
        return self._determine_routing(lead_score, conversation, client_info)

    def _check_immediate_escalation(self, current_message: str, conversation: list) -> Dict[str, Any]:
        """Check for immediate escalation triggers"""

        all_text = current_message.lower()
        for msg in conversation:
            if msg.get('role') == 'user':
                all_text += " " + msg.get('content', '').lower()

        for trigger in self.immediate_escalation_triggers:
            if trigger in all_text:
                self.log(f"⚠️ IMMEDIATE ESCALATION TRIGGERED: {trigger}")

                return {
                    'escalation_needed': True,
                    'escalation_type': 'immediate',
                    'reason': f'Detected: {trigger}',
                    'route_to': {
                        'role': 'intake_coordinator',
                        'name': 'On-Duty Staff',
                        'reason': 'Immediate human attention required'
                    },
                    'client_message': "I understand this is a serious situation. Let me connect you with someone who can help right away. Please stay on the line.",
                    'internal_notes': f'URGENT: Client mentioned "{trigger}". Immediate human contact required.',
                    'urgency': 'immediate',
                    'call_911': trigger in ['currently in danger', 'child in danger', 'domestic violence', 'active crime']
                }

        return {'escalation_needed': False}

    def _determine_routing(self, lead_score: dict, conversation: list, client_info: dict) -> Dict[str, Any]:
        """Determine appropriate routing based on case characteristics"""

        rating = lead_score.get('rating', 'WARM')
        case_type = lead_score.get('case_type', '').lower()
        estimated_value = lead_score.get('estimated_value', 'unknown')
        key_factors = [f.lower() for f in lead_score.get('key_factors', [])]

        # Priority routing criteria
        priority_indicators = [
            'commercial vehicle', 'trucking', 'semi', '18-wheeler',
            'wrongful death', 'death', 'fatality',
            'catastrophic', 'paralysis', 'brain injury', 'amputation',
            'medical malpractice', 'surgical error',
            'minor', 'child', 'children',
            'government', 'city', 'state', 'federal',
            'media', 'news', 'high profile'
        ]

        is_priority = any(ind in case_type or any(ind in f for f in key_factors)
                         for ind in priority_indicators)

        if rating == 'HOT' and (is_priority or estimated_value == 'high'):
            # Route to senior partner
            return {
                'escalation_needed': True,
                'escalation_type': 'priority',
                'reason': f'High-value {case_type} - requires senior review',
                'route_to': {
                    'role': 'senior_partner',
                    'name': self.attorneys['senior_partner']['name'],
                    'reason': 'Case complexity and potential value warrant senior attorney review'
                },
                'client_message': "Based on what you've shared, I'd like to connect you with one of our senior attorneys who specializes in cases like yours. They'll reach out within a few hours.",
                'internal_notes': f'HOT lead, high-value case. Rating: {rating}, Type: {case_type}. Recommend priority callback.',
                'urgency': 'same_day'
            }

        elif rating == 'HOT':
            # Route to PI associate for quick callback
            return {
                'escalation_needed': True,
                'escalation_type': 'standard',
                'reason': 'HOT lead - prompt attorney callback needed',
                'route_to': {
                    'role': 'pi_associate',
                    'name': self.attorneys['pi_associate_1']['name'],
                    'reason': 'Good case for associate handling, quick turnaround important'
                },
                'client_message': "Thank you for sharing all of this. An attorney from our team will call you within a few hours to discuss your case in detail.",
                'internal_notes': f'HOT lead, standard PI case. Quick callback recommended.',
                'urgency': 'same_day'
            }

        elif rating == 'WARM':
            # Route to intake coordinator for follow-up
            return {
                'escalation_needed': True,
                'escalation_type': 'standard',
                'reason': 'Warm lead - standard intake follow-up',
                'route_to': {
                    'role': 'intake_coordinator',
                    'name': self.attorneys['intake_coordinator']['name'],
                    'reason': 'Standard intake process, coordinator to gather additional info'
                },
                'client_message': "Thank you for reaching out. Our intake coordinator will follow up with you within 24 hours to discuss next steps.",
                'internal_notes': f'WARM lead. Standard follow-up process.',
                'urgency': '24_hours'
            }

        else:
            # Cold lead - gentle decline or referral
            return {
                'escalation_needed': False,
                'escalation_type': 'none',
                'reason': 'Case may not meet criteria for representation',
                'route_to': None,
                'client_message': "Thank you for reaching out. Based on what you've shared, this may not be the type of case our firm handles, but I'll have someone review your information and follow up if we can help.",
                'internal_notes': f'COLD lead. Review for possible referral to another firm.',
                'urgency': 'standard'
            }

    def get_available_attorney(self, specialties_needed: list, urgency: str) -> Optional[Dict]:
        """Get the best available attorney for routing"""

        # In production, this would check actual calendars and availability
        for attorney_id, attorney in self.attorneys.items():
            if attorney.get('role') == 'initial_screening':
                continue  # Skip coordinators for attorney routing

            attorney_specialties = attorney.get('specialties', [])
            if any(s in attorney_specialties for s in specialties_needed) or 'all' in attorney_specialties:
                return {
                    'id': attorney_id,
                    **attorney
                }

        # Fallback to intake coordinator
        return {
            'id': 'intake_coordinator',
            **self.attorneys['intake_coordinator']
        }

    def create_handoff_summary(self, session_data: dict) -> str:
        """Create a summary for the human receiving the handoff"""

        lead_score = session_data.get('lead_score', {})
        conversation = session_data.get('conversation', [])
        client_info = session_data.get('client_info', {})

        summary_parts = [
            "=" * 50,
            "CASE HANDOFF SUMMARY",
            "=" * 50,
            f"\nCLIENT: {client_info.get('name', 'Unknown')}",
            f"PHONE: {client_info.get('phone', 'Unknown')}",
            f"EMAIL: {client_info.get('email', 'Not provided')}",
            f"\nLEAD SCORE: {lead_score.get('rating', 'N/A')} ({lead_score.get('score', 'N/A')})",
            f"CASE TYPE: {lead_score.get('case_type', 'N/A')}",
            f"ESTIMATED VALUE: {lead_score.get('estimated_value', 'Unknown')}",
            f"URGENCY: {lead_score.get('urgency', 'Standard')}",
            f"\nKEY FACTORS:",
        ]

        for factor in lead_score.get('key_factors', []):
            summary_parts.append(f"  • {factor}")

        if lead_score.get('red_flags'):
            summary_parts.append(f"\n⚠️ RED FLAGS:")
            for flag in lead_score.get('red_flags', []):
                summary_parts.append(f"  • {flag}")

        summary_parts.append(f"\nRECOMMENDED ACTION: {lead_score.get('recommended_action', 'Review and contact')}")

        summary_parts.append(f"\nCONVERSATION HIGHLIGHTS:")
        for msg in conversation:
            if msg.get('role') == 'user':
                content = msg.get('content', '')[:150]
                summary_parts.append(f"  Client: {content}...")

        summary_parts.append("\n" + "=" * 50)

        return "\n".join(summary_parts)


# Quick test
if __name__ == "__main__":
    agent = HandoffAgent()

    # Test priority routing
    test_data = {
        'lead_score': {
            'rating': 'HOT',
            'score': 92,
            'case_type': 'Personal Injury - Commercial Trucking Accident',
            'key_factors': ['Commercial vehicle', 'Serious injuries', 'Clear liability'],
            'estimated_value': 'high'
        },
        'conversation': [
            {'role': 'user', 'content': 'I was hit by an Amazon truck that ran a red light'},
            {'role': 'user', 'content': 'I have a broken leg and fractured ribs'}
        ],
        'client_info': {
            'name': 'John Smith',
            'phone': '555-123-4567'
        }
    }

    result = agent.process(test_data)
    print("Routing result:", result)

    print("\n" + agent.create_handoff_summary(test_data))
