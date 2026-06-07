"""
Memory manager — unified interface to all three memory layers.
Instantiated once by ComplianceAgent and shared across the analysis pipeline.
"""

from agent.memory.episodic       import EpisodicMemory
from agent.memory.semantic       import SemanticMemory
from agent.memory.pattern_engine import PatternEngine


class MemoryManager:
    def __init__(self):
        self.episodic       = EpisodicMemory()
        self.semantic       = SemanticMemory()
        self.pattern_engine = PatternEngine(self.episodic)
