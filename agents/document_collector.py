"""
Document Collector Agent - Engine Room AI
Gathers evidence, photos, medical records authorizations, police reports
"""

from typing import Dict, Any, List
from datetime import datetime
from .base_agent import BaseAgent


class DocumentCollectorAgent(BaseAgent):
    """Collects documents and evidence needed for case evaluation"""

    def __init__(self):
        super().__init__(
            name="DocumentCollector",
            description="Gathers evidence, photos, and document authorizations from clients"
        )

    def get_system_prompt(self) -> str:
        return """You are a document collection specialist for a personal injury law firm.
Your job is to help clients understand what documents we need and guide them through providing them.

DOCUMENTS WE TYPICALLY NEED BY CASE TYPE:

AUTO ACCIDENTS:
- Photos of vehicle damage (all angles)
- Photos of injuries (bruises, cuts, etc.)
- Police report number or copy
- Other driver's insurance info
- Witness contact information
- Medical records release authorization (we provide form)
- Medical bills and records
- Lost wage documentation from employer

SLIP AND FALL:
- Photos of hazard that caused fall
- Photos of injuries
- Incident report (from store/property)
- Witness contact info
- Your shoes worn that day (preserve them)
- Medical records and bills

MEDICAL MALPRACTICE:
- All medical records related to treatment
- Names of all treating physicians
- Medical records release authorization
- Timeline of symptoms and treatment
- Second opinion documentation if obtained

WORKPLACE INJURY:
- Incident report filed with employer
- Workers comp claim number
- Photos of injury and workplace hazard
- Witness statements
- Medical records
- Employment records (pay stubs for lost wages)

HOW TO REQUEST DOCUMENTS:
- Be specific about what you need
- Explain WHY it helps their case (motivates compliance)
- Offer alternatives (photo vs scan, email vs text)
- Give deadlines but be flexible
- Prioritize - ask for most critical items first

TONE:
- Helpful, not demanding
- Explain this strengthens THEIR case
- Make it easy - accept photos via text, email, etc.
- Follow up gently if they don't respond

OUTPUT FORMAT when requesting docs:
{
    "documents_requested": [
        {
            "item": "<document name>",
            "priority": "critical" | "important" | "helpful",
            "why_needed": "<brief explanation>",
            "how_to_provide": "<instructions>",
            "deadline": "<suggested deadline>"
        }
    ],
    "message_to_client": "<the actual message to send>",
    "follow_up_in_days": <number>
}"""

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Determine what documents to request based on case type"""

        lead_score = input_data.get('lead_score', {})
        conversation = input_data.get('conversation', [])
        client_info = input_data.get('client_info', {})
        action = input_data.get('action', 'request_documents')

        case_type = lead_score.get('case_type', 'Personal Injury')

        if action == 'request_documents':
            return self._generate_document_request(case_type, lead_score, client_info)
        elif action == 'send_forms':
            return self._get_required_forms(case_type)
        elif action == 'check_status':
            return self._check_document_status(input_data.get('session_id'))

        return {'error': 'Unknown action'}

    def _generate_document_request(self, case_type: str, lead_score: dict, client_info: dict) -> Dict[str, Any]:
        """Generate a document request message"""

        messages = [{
            "role": "user",
            "content": f"""Generate a document request for this case:

CASE TYPE: {case_type}
LEAD RATING: {lead_score.get('rating', 'WARM')}
KEY FACTORS: {', '.join(lead_score.get('key_factors', []))}
CLIENT NAME: {client_info.get('name', 'Client')}

Create a friendly but specific document request. Prioritize the most critical items.
Return as JSON with documents_requested array and message_to_client."""
        }]

        response = self.call_claude(messages)

        try:
            import json
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            doc_request = json.loads(response.strip())
            self.log(f"Generated document request for {case_type}")
            return {'document_request': doc_request}
        except:
            return {'document_request': {'message_to_client': response}}

    def _get_required_forms(self, case_type: str) -> Dict[str, Any]:
        """Get list of standard forms needed"""

        standard_forms = {
            'medical_release': {
                'name': 'Medical Records Release Authorization',
                'description': 'Allows us to obtain your medical records',
                'required': True,
                'template_id': 'HIPAA_AUTH_001'
            },
            'representation_agreement': {
                'name': 'Representation Agreement',
                'description': 'Formal agreement for us to represent you',
                'required': True,
                'template_id': 'REP_AGREE_001'
            },
            'incident_questionnaire': {
                'name': 'Detailed Incident Questionnaire',
                'description': 'Helps us understand exactly what happened',
                'required': True,
                'template_id': 'INCIDENT_Q_001'
            }
        }

        # Add case-specific forms
        if 'auto' in case_type.lower() or 'car' in case_type.lower():
            standard_forms['vehicle_damage'] = {
                'name': 'Vehicle Damage Documentation Form',
                'description': 'Details about your vehicle and damage',
                'required': True,
                'template_id': 'VEH_DMG_001'
            }

        if 'workplace' in case_type.lower() or 'work' in case_type.lower():
            standard_forms['employment_verification'] = {
                'name': 'Employment and Wage Verification',
                'description': 'Documents your employment and lost wages',
                'required': True,
                'template_id': 'EMP_VERIFY_001'
            }

        return {
            'forms': standard_forms,
            'case_type': case_type,
            'instructions': 'We will email these forms to you. Please complete and return within 48 hours to expedite your case.'
        }

    def _check_document_status(self, session_id: str) -> Dict[str, Any]:
        """Check what documents have been received (placeholder for real tracking)"""

        # In production, this would check a database
        return {
            'session_id': session_id,
            'status': 'pending',
            'received': [],
            'outstanding': ['medical_release', 'photos', 'police_report'],
            'message': 'Waiting for client to submit documents'
        }

    def generate_reminder(self, client_info: dict, outstanding_docs: list) -> str:
        """Generate a friendly reminder for outstanding documents"""

        messages = [{
            "role": "user",
            "content": f"""Generate a friendly reminder message for {client_info.get('name', 'the client')}.

Outstanding documents needed:
{', '.join(outstanding_docs)}

Keep it short, friendly, and emphasize this helps THEIR case move forward faster.
Don't be pushy. Offer to help if they're having trouble."""
        }]

        return self.call_claude(messages)


# Quick test
if __name__ == "__main__":
    agent = DocumentCollectorAgent()

    test_data = {
        'lead_score': {
            'rating': 'HOT',
            'case_type': 'Personal Injury - Auto Accident',
            'key_factors': ['Clear liability', 'Medical treatment', 'Recent incident']
        },
        'client_info': {
            'name': 'Maria Garcia',
            'phone': '555-987-6543',
            'email': 'maria.g@email.com'
        },
        'action': 'request_documents'
    }

    result = agent.process(test_data)
    print(result)
