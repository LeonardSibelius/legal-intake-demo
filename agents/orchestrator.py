"""
Agent Orchestrator - Engine Room AI
Coordinates the FULL TEAM of 8 AI agents for law firm domination
"""

from typing import Dict, Any, Optional
from datetime import datetime

from .intake_agent import IntakeAgent
from .lead_scorer import LeadScoringAgent
from .spanish_agent import SpanishAgent
from .followup_agent import FollowupAgent
from .scheduler_agent import SchedulerAgent
from .document_collector import DocumentCollectorAgent
from .research_agent import ResearchAgent
from .handoff_agent import HandoffAgent


class LegalAgentOrchestrator:
    """
    THE ENGINE ROOM - 8 AI Agents Working as One Team

    This is what NO competitor has:
    ┌─────────────────────────────────────────────────────────────┐
    │                    ENGINE ROOM AI                          │
    │                                                             │
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
    │  │ INTAKE   │  │ SPANISH  │  │  LEAD    │  │ FOLLOWUP │   │
    │  │  AGENT   │  │  AGENT   │  │ SCORER   │  │  AGENT   │   │
    │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
    │       │              │              │              │        │
    │       └──────────────┴──────────────┴──────────────┘        │
    │                          │                                  │
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
    │  │SCHEDULER │  │   DOC    │  │ RESEARCH │  │ HANDOFF  │   │
    │  │  AGENT   │  │COLLECTOR │  │  AGENT   │  │  AGENT   │   │
    │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
    └─────────────────────────────────────────────────────────────┘

    24/7 • English & Spanish • Never sleeps • Never forgets
    """

    def __init__(self):
        # Initialize all 8 agents
        self.agents = {
            'intake': IntakeAgent(),
            'spanish': SpanishAgent(),
            'lead_scorer': LeadScoringAgent(),
            'followup': FollowupAgent(),
            'scheduler': SchedulerAgent(),
            'document_collector': DocumentCollectorAgent(),
            'research': ResearchAgent(),
            'handoff': HandoffAgent()
        }

        # Track active sessions
        self.sessions: Dict[str, Dict] = {}

        print("""
╔═══════════════════════════════════════════════════════════════╗
║               ENGINE ROOM AI - LEGAL AGENT SYSTEM              ║
║                                                                 ║
║   "We don't sell you a chatbot. We give you a team."           ║
╠═══════════════════════════════════════════════════════════════╣
║  AGENTS ONLINE:                                                 ║
║    ✓ Intake Agent        - Primary conversation                ║
║    ✓ Spanish Agent       - Bilingual capability                ║
║    ✓ Lead Scorer         - HOT/WARM/COLD classification        ║
║    ✓ Follow-up Agent     - SMS & email sequences               ║
║    ✓ Scheduler Agent     - Appointment booking                 ║
║    ✓ Document Collector  - Evidence gathering                  ║
║    ✓ Research Agent      - Legal research & statutes           ║
║    ✓ Handoff Agent       - Human escalation & routing          ║
╠═══════════════════════════════════════════════════════════════╣
║  STATUS: ALL SYSTEMS OPERATIONAL                                ║
╚═══════════════════════════════════════════════════════════════╝
        """)

    # ==================== SESSION MANAGEMENT ====================

    def start_session(self, session_id: str, initial_message: str) -> Dict[str, Any]:
        """Start a new intake session"""

        # Detect language
        language = self._detect_language(initial_message)

        # Create session
        self.sessions[session_id] = {
            'started_at': datetime.now().isoformat(),
            'language': language,
            'status': 'active',
            'conversation': [],
            'client_info': {},
            'lead_score': None,
            'research': None,
            'documents': {'requested': [], 'received': []},
            'appointments': [],
            'follow_ups': [],
            'handoff': None,
            'agents_used': ['intake' if language == 'english' else 'spanish']
        }

        # Route to appropriate intake agent
        if language == 'spanish':
            result = self.agents['spanish'].process({
                'message': initial_message,
                'conversation': []
            })
            self.sessions[session_id]['conversation'] = [
                {'role': 'user', 'content': initial_message},
                {'role': 'assistant', 'content': result['response']}
            ]
        else:
            result = self.agents['intake'].process({
                'message': initial_message,
                'conversation_id': session_id
            })
            self.sessions[session_id]['conversation'] = result.get('conversation', [])

        return {
            'response': result['response'],
            'session_id': session_id,
            'language': language,
            'agent': 'spanish' if language == 'spanish' else 'intake'
        }

    def continue_session(self, session_id: str, message: str) -> Dict[str, Any]:
        """Continue an existing intake session"""

        if session_id not in self.sessions:
            return self.start_session(session_id, message)

        session = self.sessions[session_id]

        # Check for immediate escalation first
        handoff_check = self.agents['handoff'].process({
            'current_message': message,
            'conversation': session['conversation'],
            'lead_score': session.get('lead_score', {}),
            'client_info': session.get('client_info', {})
        })

        if handoff_check.get('escalation_type') == 'immediate':
            session['handoff'] = handoff_check
            session['status'] = 'escalated'
            return {
                'response': handoff_check['client_message'],
                'escalated': True,
                'urgency': 'immediate'
            }

        # Continue with appropriate intake agent
        if session['language'] == 'spanish':
            result = self.agents['spanish'].process({
                'message': message,
                'conversation': session['conversation']
            })
            session['conversation'].append({'role': 'user', 'content': message})
            session['conversation'].append({'role': 'assistant', 'content': result['response']})
        else:
            result = self.agents['intake'].process({
                'message': message,
                'conversation_id': session_id
            })
            session['conversation'] = result.get('conversation', session['conversation'])

        return {
            'response': result['response'],
            'session_id': session_id,
            'message_count': len(session['conversation'])
        }

    # ==================== FULL PIPELINE ====================

    def complete_intake(self, session_id: str, state: str = 'Nevada') -> Dict[str, Any]:
        """
        Complete intake and run the FULL 8-agent pipeline:
        1. Score the lead (LeadScorer)
        2. Conduct legal research (ResearchAgent)
        3. Determine routing (HandoffAgent)
        4. Generate follow-up sequence (FollowupAgent)
        5. Request documents (DocumentCollector)
        6. Schedule appointment for HOT leads (SchedulerAgent)
        """

        if session_id not in self.sessions:
            return {'error': 'Session not found'}

        session = self.sessions[session_id]
        session['status'] = 'processing'
        results = {}

        print(f"\n{'='*60}")
        print(f"RUNNING FULL AGENT PIPELINE - Session: {session_id}")
        print(f"{'='*60}\n")

        # 1. LEAD SCORING
        print("📊 [1/6] Lead Scoring Agent analyzing...")
        score_result = self.agents['lead_scorer'].process({
            'conversation': session['conversation'],
            'client_info': session.get('client_info', {})
        })
        session['lead_score'] = score_result.get('lead_score', {})
        results['lead_score'] = session['lead_score']
        session['agents_used'].append('lead_scorer')
        print(f"   → Rating: {session['lead_score'].get('rating')} ({session['lead_score'].get('score')})")

        # 2. LEGAL RESEARCH
        print("\n📚 [2/6] Research Agent conducting legal research...")
        research_result = self.agents['research'].process({
            'lead_score': session['lead_score'],
            'conversation': session['conversation'],
            'client_info': session.get('client_info', {}),
            'state': state,
            'research_type': 'full'
        })
        session['research'] = research_result.get('research', {})
        results['research'] = session['research']
        session['agents_used'].append('research')
        print(f"   → Research complete")

        # 3. HANDOFF/ROUTING DETERMINATION
        print("\n🔀 [3/6] Handoff Agent determining routing...")
        handoff_result = self.agents['handoff'].process({
            'lead_score': session['lead_score'],
            'conversation': session['conversation'],
            'client_info': session.get('client_info', {})
        })
        session['handoff'] = handoff_result
        results['handoff'] = handoff_result
        session['agents_used'].append('handoff')
        print(f"   → Route to: {handoff_result.get('route_to', {}).get('role', 'N/A')}")
        print(f"   → Urgency: {handoff_result.get('urgency', 'standard')}")

        # 4. FOLLOW-UP SEQUENCE
        print("\n📧 [4/6] Follow-up Agent generating sequences...")
        sequence = self.agents['followup'].generate_sequence(
            session['lead_score'],
            session.get('client_info', {})
        )
        session['follow_up_sequence'] = sequence

        first_followup = self.agents['followup'].process({
            'lead_score': session['lead_score'],
            'conversation': session['conversation'],
            'client_info': session.get('client_info', {}),
            'follow_up_stage': 1,
            'channel': sequence[0]['channel'] if sequence else 'email'
        })
        results['follow_up'] = {
            'sequence': sequence,
            'first_message': first_followup.get('follow_up', {})
        }
        session['agents_used'].append('followup')
        print(f"   → {len(sequence)} follow-ups scheduled")

        # 5. DOCUMENT COLLECTION
        print("\n📄 [5/6] Document Collector requesting evidence...")
        doc_result = self.agents['document_collector'].process({
            'lead_score': session['lead_score'],
            'client_info': session.get('client_info', {}),
            'action': 'request_documents'
        })
        session['documents']['requested'] = doc_result.get('document_request', {})
        results['documents'] = doc_result
        session['agents_used'].append('document_collector')
        print(f"   → Document request generated")

        # 6. SCHEDULING (for HOT leads)
        rating = session['lead_score'].get('rating', 'WARM')
        if rating == 'HOT':
            print("\n🔥 [6/6] Scheduler Agent booking priority appointment...")
            schedule_result = self.agents['scheduler'].process({
                'action': 'suggest_times',
                'lead_score': session['lead_score'],
                'client_info': session.get('client_info', {})
            })
            results['scheduling'] = schedule_result
            session['agents_used'].append('scheduler')
            print(f"   → Appointment times suggested")
        else:
            print("\n⏭️  [6/6] Scheduler Agent skipped (not HOT lead)")
            results['scheduling'] = None

        # Generate final summary
        session['status'] = 'completed'
        results['session_summary'] = self._generate_summary(session)
        results['handoff_summary'] = self.agents['handoff'].create_handoff_summary({
            'lead_score': session['lead_score'],
            'conversation': session['conversation'],
            'client_info': session.get('client_info', {})
        })

        print(f"\n{'='*60}")
        print(f"PIPELINE COMPLETE - {len(session['agents_used'])} agents used")
        print(f"{'='*60}\n")

        return results

    # ==================== UTILITY METHODS ====================

    def _detect_language(self, text: str) -> str:
        """Detect if text is Spanish or English"""
        spanish_words = ['hola', 'necesito', 'ayuda', 'accidente', 'abogado',
                        'tengo', 'por favor', 'gracias', 'buenas', 'días']
        text_lower = text.lower()
        spanish_count = sum(1 for word in spanish_words if word in text_lower)
        return 'spanish' if spanish_count >= 2 else 'english'

    def _generate_summary(self, session: Dict) -> str:
        """Generate a summary of the intake session"""
        score = session.get('lead_score', {})
        return f"""
╔══════════════════════════════════════════════════════════════╗
║                    INTAKE COMPLETE                            ║
╠══════════════════════════════════════════════════════════════╣
║  Rating: {score.get('rating', 'N/A'):8} Score: {str(score.get('score', 'N/A')):3}                       ║
║  Case Type: {score.get('case_type', 'N/A')[:40]:40}   ║
║  Urgency: {score.get('urgency', 'N/A'):10}                                    ║
║  Est. Value: {score.get('estimated_value', 'unknown'):10}                              ║
╠══════════════════════════════════════════════════════════════╣
║  Key Factors:                                                 ║
{self._format_list(score.get('key_factors', []))}║  Red Flags:                                                   ║
{self._format_list(score.get('red_flags', []) or ['None'])}╠══════════════════════════════════════════════════════════════╣
║  Recommended: {score.get('recommended_action', 'N/A')[:45]:45}║
║  Messages: {len(session.get('conversation', [])):3}    Language: {session.get('language', 'english'):8}              ║
║  Agents Used: {len(session.get('agents_used', [])):1}                                             ║
╚══════════════════════════════════════════════════════════════╝
"""

    def _format_list(self, items: list) -> str:
        """Format a list for the summary box"""
        lines = []
        for item in items[:3]:  # Max 3 items
            lines.append(f"║    • {item[:50]:50}   ║\n")
        return ''.join(lines) if lines else "║    • None                                              ║\n"

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        return self.sessions.get(session_id)

    def get_all_sessions(self) -> Dict[str, Dict]:
        """Get all sessions (for admin dashboard)"""
        return self.sessions

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        total = len(self.sessions)
        active = sum(1 for s in self.sessions.values() if s['status'] == 'active')
        completed = sum(1 for s in self.sessions.values() if s['status'] == 'completed')

        scores = [s.get('lead_score', {}).get('rating') for s in self.sessions.values()]
        hot = scores.count('HOT')
        warm = scores.count('WARM')
        cold = scores.count('COLD')

        return {
            'total_sessions': total,
            'active_sessions': active,
            'completed_sessions': completed,
            'leads': {'hot': hot, 'warm': warm, 'cold': cold},
            'agents_online': len(self.agents),
            'agent_names': list(self.agents.keys())
        }


# ==================== DEMO / TEST ====================

if __name__ == "__main__":
    orchestrator = LegalAgentOrchestrator()

    print("\n" + "="*60)
    print("SIMULATING FULL INTAKE CONVERSATION")
    print("="*60 + "\n")

    session_id = "demo_session_001"

    # Start conversation
    result = orchestrator.start_session(
        session_id,
        "Hi, I was hit by an Amazon delivery truck yesterday while stopped at a red light"
    )
    print(f"CLIENT: Hi, I was hit by an Amazon delivery truck yesterday...")
    print(f"AGENT: {result['response']}\n")

    # Continue conversation
    messages = [
        "Yes, I'm in a lot of pain. I went to the ER and they said I have whiplash and a fractured rib",
        "The truck driver ran the red light. A police officer came and gave him a ticket. There were witnesses too",
        "I'm worried about my medical bills and I can't work right now",
        "My name is Maria Garcia, you can reach me at 555-123-4567"
    ]

    for msg in messages:
        print(f"CLIENT: {msg}")
        result = orchestrator.continue_session(session_id, msg)
        print(f"AGENT: {result['response']}\n")

    # Run full pipeline
    print("\n" + "="*60)
    print("RUNNING FULL 8-AGENT PIPELINE")
    print("="*60)

    final_result = orchestrator.complete_intake(session_id, state='Nevada')

    print(final_result['session_summary'])

    print("\n📋 HANDOFF SUMMARY FOR ATTORNEY:")
    print(final_result['handoff_summary'])

    # Show stats
    print("\n📊 SYSTEM STATS:")
    stats = orchestrator.get_stats()
    print(f"   Agents Online: {stats['agents_online']}")
    print(f"   Sessions: {stats['total_sessions']}")
    print(f"   Leads: HOT={stats['leads']['hot']}, WARM={stats['leads']['warm']}, COLD={stats['leads']['cold']}")
