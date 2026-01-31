# Engine Room AI - Legal Agent System
# Multi-agent architecture for law firm automation
#
# "We don't sell you a chatbot. We give you a team."
#
# 8 Specialized Agents:
# 1. IntakeAgent - Primary conversation handler
# 2. LeadScoringAgent - HOT/WARM/COLD classification
# 3. SpanishAgent - Bilingual intake (English/Spanish)
# 4. FollowupAgent - SMS/email nurture sequences
# 5. SchedulerAgent - Appointment booking
# 6. DocumentCollectorAgent - Evidence & records gathering
# 7. ResearchAgent - Legal research & statute lookups
# 8. HandoffAgent - Human escalation & routing

from .base_agent import BaseAgent, AgentOrchestrator
from .intake_agent import IntakeAgent
from .lead_scorer import LeadScoringAgent
from .spanish_agent import SpanishAgent
from .followup_agent import FollowupAgent
from .scheduler_agent import SchedulerAgent
from .document_collector import DocumentCollectorAgent
from .research_agent import ResearchAgent
from .handoff_agent import HandoffAgent
from .orchestrator import LegalAgentOrchestrator

__all__ = [
    'BaseAgent',
    'AgentOrchestrator',
    'IntakeAgent',
    'LeadScoringAgent',
    'SpanishAgent',
    'FollowupAgent',
    'SchedulerAgent',
    'DocumentCollectorAgent',
    'ResearchAgent',
    'HandoffAgent',
    'LegalAgentOrchestrator'
]

__version__ = '1.0.0'
__author__ = 'Engine Room AI'
