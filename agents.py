import os
from crewai import Agent

# CrewAI stable model identifier
llm_string = "gemini-3-flash-preview"

class CCAAgents:
    def research_agent(self):
        return Agent(
            role='Empirical Researcher',
            goal='Provide objective, data-driven facts and historical precedents.',
            backstory='A world-class data scientist. You provide the evidence required to ground any debate.',
            llm=llm_string, verbose=True, allow_delegation=False
        )

    def debate_agent(self):
        return Agent(
            role='Adversarial Strategist',
            goal='Identify logical fallacies and systemic risks in the user’s proposition.',
            backstory='Master of Red Teaming. You find why ideas fail, but you must stay grounded in research.',
            llm=llm_string, verbose=True, allow_delegation=False
        )

    def teacher_agent(self):
        return Agent(
            role='Socratic Master & Safety Officer',
            goal='Synthesize research and debate into a safe, grounded Socratic inquiry.',
            backstory="""You are the final arbiter. Your job is to ensure the Debater's 
            friction is constructive and factually grounded. If the Debater hallucinates, 
            you must correct it. You use analogies to lead the user to breakthroughs.""",
            llm=llm_string, verbose=True, allow_delegation=False
        )

    def cognitive_architect(self):
        return Agent(
            role='Cognitive Architect & Learning Planner',
            goal='Audit reasoning patterns and architect a proactive learning roadmap.',
            backstory="""Expert in metacognition. You compare current sessions with 
            past profiles to track intellectual evolution and suggest [READ/EXPERIMENT] quests.""",
            llm=llm_string, verbose=True, allow_delegation=False
        )