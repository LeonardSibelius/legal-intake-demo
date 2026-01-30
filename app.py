"""
Legal Client Intake Demo - Engine Room AI
A 24/7 AI assistant that handles initial client intake for law firms.
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import anthropic

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'legal-demo-secret-key-2026')
CORS(app)

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

# Demo password
DEMO_PASSWORD = os.environ.get('DEMO_PASSWORD', 'legalintake2026')

# System prompt for the legal intake assistant
SYSTEM_PROMPT = """You are a friendly, professional legal intake assistant for a general practice law firm. Your job is to:

1. Warmly greet potential clients and make them feel heard
2. Understand their legal situation (what type of issue they're facing)
3. Gather essential information for the attorneys
4. Identify any urgent time-sensitive matters

PRACTICE AREAS you can help with:
- Personal Injury (car accidents, slip & fall, medical malpractice)
- Family Law (divorce, custody, child support, adoption)
- Criminal Defense (DUI, misdemeanors, felonies)
- Estate Planning (wills, trusts, probate)
- Business Law (contracts, formation, disputes)
- Real Estate (transactions, disputes, landlord-tenant)
- Employment Law (wrongful termination, discrimination, wage disputes)
- Immigration (visas, green cards, citizenship)

INFORMATION TO GATHER (naturally, through conversation):
- Name and contact information
- Type of legal issue
- Brief description of the situation
- Any important dates or deadlines
- How they heard about the firm (optional)

IMPORTANT GUIDELINES:
- Be empathetic - people reaching out to lawyers are often stressed
- NEVER provide legal advice - you're gathering information only
- If someone describes an emergency (arrest, immediate harm), tell them to call 911 or the office directly
- Keep responses concise but warm (2-3 sentences usually)
- After gathering info, let them know an attorney will review and contact them within 24 hours
- If asked about fees, say "Our attorneys offer free initial consultations for most matters"

When you have enough information, summarize what you've learned and confirm their contact details.

Remember: You represent a professional law firm. Be helpful but maintain appropriate boundaries."""

# Store conversations (in production, use a database)
conversations = {}

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
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Invalid password'})

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.json
    user_message = data.get('message', '')
    conversation_id = data.get('conversation_id', 'default')

    # Get or create conversation history
    if conversation_id not in conversations:
        conversations[conversation_id] = []

    # Add user message to history
    conversations[conversation_id].append({
        "role": "user",
        "content": user_message
    })

    try:
        # Call Claude API
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=conversations[conversation_id]
        )

        assistant_message = response.content[0].text

        # Add assistant response to history
        conversations[conversation_id].append({
            "role": "assistant",
            "content": assistant_message
        })

        return jsonify({
            'response': assistant_message,
            'conversation_id': conversation_id
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset_conversation():
    """Reset the conversation"""
    data = request.json
    conversation_id = data.get('conversation_id', 'default')

    if conversation_id in conversations:
        conversations[conversation_id] = []

    return jsonify({'success': True})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'demo': 'legal-intake'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
