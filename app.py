"""
Legal Client Intake Demo - Engine Room AI
8-Agent Multi-Agent System for Law Firm Domination

"We don't sell you a chatbot. We give you a team."
"""

import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import anthropic

# Import our 8-agent system
from agents import LegalAgentOrchestrator

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'legal-demo-secret-key-2026')
CORS(app)

# Initialize the 8-agent orchestrator
orchestrator = LegalAgentOrchestrator()

# Demo password
DEMO_PASSWORD = os.environ.get('DEMO_PASSWORD', 'legalintake2026')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/verify', methods=['POST'])
def verify_password():
    """Verify demo access password"""
    data = request.json
    password = data.get('password', '')

    if password == DEMO_PASSWORD:
        session['authenticated'] = True
        # Generate unique session ID for this demo user
        session['session_id'] = str(uuid.uuid4())
        return jsonify({'success': True, 'session_id': session['session_id']})
    return jsonify({'success': False, 'error': 'Invalid password'})


@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages through the 8-agent system"""
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.json
    user_message = data.get('message', '')
    session_id = session.get('session_id', 'default')

    try:
        # Check if this is a new or existing session
        existing_session = orchestrator.get_session(session_id)

        if existing_session:
            # Continue existing conversation
            result = orchestrator.continue_session(session_id, user_message)
        else:
            # Start new session
            result = orchestrator.start_session(session_id, user_message)

        # Build response with agent info
        response_data = {
            'response': result['response'],
            'session_id': session_id,
            'agent': result.get('agent', 'intake'),
            'language': result.get('language', 'english'),
            'message_count': result.get('message_count', 1)
        }

        # Check if escalation happened
        if result.get('escalated'):
            response_data['escalated'] = True
            response_data['urgency'] = result.get('urgency', 'standard')

        return jsonify(response_data)

    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/complete-intake', methods=['POST'])
def complete_intake():
    """Run the full 8-agent pipeline on a completed intake"""
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authenticated'}), 401

    session_id = session.get('session_id', 'default')
    data = request.json
    state = data.get('state', 'Nevada')  # Default to Nevada for demo

    try:
        # Run full agent pipeline
        result = orchestrator.complete_intake(session_id, state=state)

        return jsonify({
            'success': True,
            'lead_score': result.get('lead_score', {}),
            'research': result.get('research', {}),
            'handoff': result.get('handoff', {}),
            'follow_up': result.get('follow_up', {}),
            'documents': result.get('documents', {}),
            'scheduling': result.get('scheduling'),
            'summary': result.get('session_summary', ''),
            'handoff_summary': result.get('handoff_summary', '')
        })

    except Exception as e:
        print(f"Complete intake error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/session-info', methods=['GET'])
def session_info():
    """Get current session information"""
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authenticated'}), 401

    session_id = session.get('session_id', 'default')
    session_data = orchestrator.get_session(session_id)

    if session_data:
        return jsonify({
            'session_id': session_id,
            'status': session_data.get('status', 'unknown'),
            'language': session_data.get('language', 'english'),
            'message_count': len(session_data.get('conversation', [])),
            'lead_score': session_data.get('lead_score'),
            'agents_used': session_data.get('agents_used', [])
        })

    return jsonify({'session_id': session_id, 'status': 'no_session'})


@app.route('/reset', methods=['POST'])
def reset_conversation():
    """Reset the conversation and start fresh"""
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authenticated'}), 401

    # Generate new session ID
    session['session_id'] = str(uuid.uuid4())

    return jsonify({
        'success': True,
        'new_session_id': session['session_id']
    })


@app.route('/stats', methods=['GET'])
def get_stats():
    """Get system statistics (admin view)"""
    stats = orchestrator.get_stats()
    return jsonify(stats)


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'demo': 'legal-intake-8-agent',
        'agents_online': 8,
        'version': '2.0.0'
    })


# ==================== DEMO ENDPOINTS ====================

@app.route('/demo/spanish', methods=['POST'])
def demo_spanish():
    """Demo endpoint showing Spanish agent in action"""
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.json
    message = data.get('message', 'Hola, necesito ayuda con un accidente')

    session_id = f"spanish_demo_{uuid.uuid4()}"
    result = orchestrator.start_session(session_id, message)

    return jsonify({
        'response': result['response'],
        'language_detected': result.get('language', 'spanish'),
        'agent': result.get('agent', 'spanish')
    })


@app.route('/demo/score-lead', methods=['POST'])
def demo_score_lead():
    """Demo endpoint showing lead scoring"""
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authenticated'}), 401

    # Use sample conversation for demo
    sample_conversation = [
        {'role': 'user', 'content': 'I was hit by an Amazon truck that ran a red light'},
        {'role': 'assistant', 'content': 'I\'m so sorry to hear that. Were you injured in the accident?'},
        {'role': 'user', 'content': 'Yes, I have a fractured rib and whiplash. I went to the ER.'},
        {'role': 'assistant', 'content': 'That sounds painful. Did the police come to the scene?'},
        {'role': 'user', 'content': 'Yes, the truck driver got a ticket. There were witnesses too.'}
    ]

    from agents import LeadScoringAgent
    scorer = LeadScoringAgent()

    result = scorer.process({
        'conversation': sample_conversation,
        'client_info': {'name': 'Demo User', 'phone': '555-123-4567'}
    })

    return jsonify({
        'lead_score': result.get('lead_score', {}),
        'sample_conversation': 'Commercial trucking accident with injuries, liability, witnesses'
    })


@app.route('/demo/agents', methods=['GET'])
def demo_agents():
    """List all 8 agents and their capabilities"""
    agents = {
        '1_intake': {
            'name': 'Intake Agent',
            'description': 'Primary conversation handler - warm, professional intake',
            'capabilities': ['Greeting', 'Fact gathering', 'Empathy', 'Initial qualification']
        },
        '2_spanish': {
            'name': 'Spanish Agent',
            'description': 'Full bilingual capability - seamless Spanish intake',
            'capabilities': ['Spanish conversation', 'Translation', 'Cultural competence']
        },
        '3_lead_scorer': {
            'name': 'Lead Scoring Agent',
            'description': 'HOT/WARM/COLD classification with detailed analysis',
            'capabilities': ['Score 0-100', 'Case type detection', 'Value estimation', 'Red flag detection']
        },
        '4_followup': {
            'name': 'Follow-up Agent',
            'description': 'SMS and email nurture sequences',
            'capabilities': ['Sequence generation', 'Channel optimization', 'Timing strategy']
        },
        '5_scheduler': {
            'name': 'Scheduler Agent',
            'description': 'Appointment booking and calendar management',
            'capabilities': ['Availability check', 'Priority scheduling', 'Confirmation']
        },
        '6_document_collector': {
            'name': 'Document Collector Agent',
            'description': 'Evidence and records gathering',
            'capabilities': ['Document requests', 'Checklist generation', 'Status tracking']
        },
        '7_research': {
            'name': 'Research Agent',
            'description': 'Legal research and statute lookups',
            'capabilities': ['Statute of limitations', 'Liability frameworks', 'State laws']
        },
        '8_handoff': {
            'name': 'Handoff Agent',
            'description': 'Human escalation and attorney routing',
            'capabilities': ['Escalation detection', 'Attorney matching', 'Summary generation']
        }
    }

    return jsonify({
        'agent_count': 8,
        'tagline': "We don't sell you a chatbot. We give you a team.",
        'agents': agents
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("""
╔═══════════════════════════════════════════════════════════════╗
║               ENGINE ROOM AI - LEGAL DEMO                      ║
║                                                                 ║
║   "We don't sell you a chatbot. We give you a team."           ║
╠═══════════════════════════════════════════════════════════════╣
║  MULTI-AGENT SYSTEM INITIALIZED                                 ║
║    • 8 Specialized AI Agents                                    ║
║    • 24/7 Operation                                             ║
║    • English & Spanish                                          ║
║    • Full Pipeline Automation                                   ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=port, debug=False)
