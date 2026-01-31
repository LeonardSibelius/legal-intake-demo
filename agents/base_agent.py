"""
Base Agent class for Engine Room AI
All specialized agents inherit from this.
"""

import os
import anthropic
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class BaseAgent(ABC):
    """Base class for all Engine Room AI agents"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        self.model = "claude-sonnet-4-20250514"
        self.max_tokens = 1000

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent"""
        pass

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return output"""
        pass

    def call_claude(self, messages: list, system_prompt: Optional[str] = None) -> str:
        """Make a call to Claude API"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt or self.get_system_prompt(),
                messages=messages
            )
            return response.content[0].text
        except Exception as e:
            return f"Error: {str(e)}"

    def log(self, message: str):
        """Log agent activity"""
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] [{self.name}] {message}")


class AgentOrchestrator:
    """Coordinates multiple agents working together"""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.conversation_state: Dict[str, Any] = {}

    def register_agent(self, agent: BaseAgent):
        """Register an agent with the orchestrator"""
        self.agents[agent.name] = agent
        print(f"Registered agent: {agent.name}")

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get an agent by name"""
        return self.agents.get(name)

    def run_pipeline(self, input_data: Dict[str, Any], pipeline: list) -> Dict[str, Any]:
        """Run a sequence of agents, passing output to next input"""
        current_data = input_data
        results = []

        for agent_name in pipeline:
            agent = self.get_agent(agent_name)
            if agent:
                agent.log(f"Processing...")
                result = agent.process(current_data)
                results.append({
                    'agent': agent_name,
                    'result': result
                })
                # Merge result into current data for next agent
                current_data = {**current_data, **result}
            else:
                print(f"Warning: Agent '{agent_name}' not found")

        return {
            'final_output': current_data,
            'pipeline_results': results
        }
