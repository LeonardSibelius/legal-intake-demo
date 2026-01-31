"""
Spanish Language Agent - Engine Room AI
Handles bilingual intake - detects Spanish and conducts intake in Spanish
"""

from typing import Dict, Any
from .base_agent import BaseAgent


class SpanishAgent(BaseAgent):
    """Bilingual intake agent - English/Spanish"""

    def __init__(self):
        super().__init__(
            name="SpanishIntake",
            description="Handles Spanish-language client intake"
        )

    def get_system_prompt(self) -> str:
        return """Eres un asistente de admisión legal profesional y amable para un bufete de abogados.
Tu trabajo es ayudar a clientes que hablan español a explicar su situación legal.

TU ROL:
1. Saludar cálidamente y hacer que el cliente se sienta escuchado
2. Entender su situación legal
3. Recopilar información esencial para los abogados
4. Identificar asuntos urgentes

ÁREAS DE PRÁCTICA:
- Lesiones Personales (accidentes de auto, caídas, negligencia médica)
- Derecho Familiar (divorcio, custodia, pensión alimenticia)
- Defensa Criminal (DUI, delitos menores y mayores)
- Planificación Patrimonial (testamentos, fideicomisos)
- Derecho de Negocios (contratos, disputas)
- Bienes Raíces (transacciones, disputas)
- Derecho Laboral (despido injusto, discriminación)
- Inmigración (visas, residencia, ciudadanía)

INFORMACIÓN A RECOPILAR:
- Nombre y información de contacto
- Tipo de problema legal
- Breve descripción de la situación
- Fechas importantes o plazos
- Cómo se enteró de nosotros (opcional)

DIRECTRICES IMPORTANTES:
- Sé empático - las personas que buscan abogados están estresadas
- NUNCA des consejos legales - solo recopilas información
- Si hay emergencia (arresto, peligro inmediato), diles que llamen al 911
- Mantén respuestas concisas pero cálidas (2-3 oraciones)
- Al final, confirma que un abogado revisará y los contactará en 24 horas
- Si preguntan por costos: "Nuestros abogados ofrecen consultas iniciales gratuitas"

Recuerda: Representas un bufete profesional. Sé útil pero mantén límites apropiados.

IMPORTANTE: Si el cliente escribe en inglés, responde en inglés. Si escribe en español, responde en español."""

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a message - detect language and respond appropriately"""

        message = input_data.get('message', '')
        conversation = input_data.get('conversation', [])

        # Add current message to conversation
        messages = conversation + [{"role": "user", "content": message}]

        response = self.call_claude(messages)

        return {
            'response': response,
            'language': self._detect_language(message),
            'agent_used': self.name
        }

    def _detect_language(self, text: str) -> str:
        """Simple language detection"""
        spanish_indicators = [
            'hola', 'necesito', 'ayuda', 'abogado', 'accidente',
            'tengo', 'quiero', 'gracias', 'buenos', 'días',
            'por favor', 'mi', 'es', 'un', 'una', 'el', 'la',
            'qué', 'cómo', 'cuándo', 'dónde', 'puedo'
        ]

        text_lower = text.lower()
        spanish_count = sum(1 for word in spanish_indicators if word in text_lower)

        return 'spanish' if spanish_count >= 2 else 'english'

    def translate_to_english(self, text: str) -> str:
        """Translate Spanish text to English for internal processing"""
        messages = [{
            "role": "user",
            "content": f"Translate this to English (just the translation, no explanation): {text}"
        }]

        return self.call_claude(messages, system_prompt="You are a translator. Translate accurately and naturally.")

    def summarize_in_english(self, conversation: list) -> str:
        """Summarize a Spanish conversation in English for attorneys"""
        conv_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation])

        messages = [{
            "role": "user",
            "content": f"""Summarize this Spanish intake conversation in English for the attorney.
Include: client name, legal issue, key facts, contact info (if given), and urgency level.

CONVERSATION:
{conv_text}"""
        }]

        return self.call_claude(messages, system_prompt="You are a bilingual legal assistant. Summarize accurately.")


# Quick test
if __name__ == "__main__":
    agent = SpanishAgent()

    # Test Spanish
    result = agent.process({
        'message': 'Hola, tuve un accidente de carro ayer y necesito ayuda',
        'conversation': []
    })
    print("Spanish test:", result)

    # Test English
    result = agent.process({
        'message': 'Hi, I was in a car accident yesterday',
        'conversation': []
    })
    print("English test:", result)
