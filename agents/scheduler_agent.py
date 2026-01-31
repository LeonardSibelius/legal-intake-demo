"""
Scheduler Agent - Engine Room AI
Handles appointment booking and calendar management
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from .base_agent import BaseAgent


class SchedulerAgent(BaseAgent):
    """Books consultations and manages attorney availability"""

    def __init__(self):
        super().__init__(
            name="SchedulerAgent",
            description="Handles appointment scheduling and calendar management"
        )
        # Simulated availability (in production, integrate with real calendar)
        self.available_slots = self._generate_available_slots()

    def get_system_prompt(self) -> str:
        return """You are a scheduling assistant for a law firm.
Your job is to help clients book consultations with attorneys.

GUIDELINES:
- Be friendly and accommodating
- Offer multiple time options when possible
- Confirm timezone if unclear
- For urgent cases, try to find same-day or next-day availability
- Always confirm the appointment details at the end

INFORMATION TO COLLECT:
- Preferred date/time
- Best phone number to reach them
- Preferred consultation type (phone, video, in-person)
- Any accessibility needs

OUTPUT FORMAT when booking:
{
    "action": "book" | "reschedule" | "cancel" | "check_availability",
    "appointment": {
        "date": "YYYY-MM-DD",
        "time": "HH:MM",
        "duration_minutes": 30,
        "type": "phone" | "video" | "in_person",
        "attorney": "<attorney name or 'next_available'>",
        "client_name": "<name>",
        "client_phone": "<phone>",
        "case_type": "<type>",
        "notes": "<any special notes>"
    },
    "confirmation_message": "<message to send to client>"
}"""

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a scheduling request"""

        action = input_data.get('action', 'check_availability')
        client_info = input_data.get('client_info', {})
        lead_score = input_data.get('lead_score', {})
        preferred_time = input_data.get('preferred_time', None)

        if action == 'check_availability':
            return self._get_availability(lead_score)

        elif action == 'book':
            return self._book_appointment(input_data)

        elif action == 'suggest_times':
            return self._suggest_times(lead_score, client_info)

        return {'error': 'Unknown action'}

    def _generate_available_slots(self) -> List[Dict]:
        """Generate simulated available time slots"""
        slots = []
        base_date = datetime.now()

        # Generate slots for next 7 business days
        for day_offset in range(1, 10):
            date = base_date + timedelta(days=day_offset)

            # Skip weekends
            if date.weekday() >= 5:
                continue

            # Morning slots
            for hour in [9, 10, 11]:
                slots.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'time': f'{hour}:00',
                    'available': True,
                    'attorney': 'Available Attorney'
                })

            # Afternoon slots
            for hour in [13, 14, 15, 16]:
                slots.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'time': f'{hour}:00',
                    'available': True,
                    'attorney': 'Available Attorney'
                })

        return slots

    def _get_availability(self, lead_score: dict) -> Dict[str, Any]:
        """Get available appointment slots"""

        rating = lead_score.get('rating', 'WARM')

        # For HOT leads, prioritize sooner slots
        if rating == 'HOT':
            slots = [s for s in self.available_slots if s['available']][:5]
            urgency_note = "Priority scheduling - earliest available times"
        else:
            slots = [s for s in self.available_slots if s['available']][:10]
            urgency_note = "Standard scheduling"

        return {
            'available_slots': slots,
            'urgency_note': urgency_note,
            'total_available': len([s for s in self.available_slots if s['available']])
        }

    def _suggest_times(self, lead_score: dict, client_info: dict) -> Dict[str, Any]:
        """Generate natural language time suggestions"""

        availability = self._get_availability(lead_score)
        slots = availability['available_slots'][:3]

        if not slots:
            return {
                'suggestion': "I apologize, but we're fully booked at the moment. Can I take your number and have someone call you when a slot opens up?",
                'slots': []
            }

        # Format slots nicely
        formatted = []
        for slot in slots:
            date_obj = datetime.strptime(slot['date'], '%Y-%m-%d')
            day_name = date_obj.strftime('%A')
            formatted.append(f"{day_name}, {date_obj.strftime('%B %d')} at {slot['time']}")

        rating = lead_score.get('rating', 'WARM')

        if rating == 'HOT':
            suggestion = f"Given the urgency of your situation, I'd like to get you in as soon as possible. I have availability {formatted[0]}. Would that work for you?"
        else:
            suggestion = f"I have a few times available this week: {', '.join(formatted)}. Which works best for you?"

        return {
            'suggestion': suggestion,
            'slots': slots
        }

    def _book_appointment(self, input_data: dict) -> Dict[str, Any]:
        """Book an appointment"""

        client_info = input_data.get('client_info', {})
        selected_slot = input_data.get('selected_slot', {})
        consultation_type = input_data.get('consultation_type', 'phone')

        # Find and mark slot as booked
        for slot in self.available_slots:
            if slot['date'] == selected_slot.get('date') and slot['time'] == selected_slot.get('time'):
                slot['available'] = False

                appointment = {
                    'date': slot['date'],
                    'time': slot['time'],
                    'duration_minutes': 30,
                    'type': consultation_type,
                    'attorney': slot['attorney'],
                    'client_name': client_info.get('name', 'Unknown'),
                    'client_phone': client_info.get('phone', 'Unknown'),
                    'case_type': input_data.get('lead_score', {}).get('case_type', 'General'),
                    'status': 'confirmed'
                }

                date_obj = datetime.strptime(slot['date'], '%Y-%m-%d')
                day_name = date_obj.strftime('%A')

                confirmation = f"You're all set! Your consultation is confirmed for {day_name}, {date_obj.strftime('%B %d')} at {slot['time']}. "
                if consultation_type == 'phone':
                    confirmation += f"An attorney will call you at {client_info.get('phone', 'your number on file')}."
                elif consultation_type == 'video':
                    confirmation += "You'll receive a video link via email shortly."
                else:
                    confirmation += "We'll see you at our office."

                self.log(f"Booked appointment for {client_info.get('name')} on {slot['date']} at {slot['time']}")

                return {
                    'appointment': appointment,
                    'confirmation_message': confirmation,
                    'success': True
                }

        return {
            'success': False,
            'error': 'Selected slot is no longer available'
        }


# Quick test
if __name__ == "__main__":
    agent = SchedulerAgent()

    # Test availability check
    result = agent.process({
        'action': 'check_availability',
        'lead_score': {'rating': 'HOT'}
    })
    print("Availability:", result)

    # Test time suggestion
    result = agent.process({
        'action': 'suggest_times',
        'lead_score': {'rating': 'HOT'},
        'client_info': {'name': 'John Smith'}
    })
    print("\nSuggestion:", result)
