"""
Reinforcement learning feedback and preference pairing module for AI-VH.
Handles Direct Preference Optimization (DPO) pairs, physician grading, and reward modeling.
"""

try:
    from backend.rl.dpo_generator import dpo_generator
except ImportError:
    dpo_generator = None

__all__ = ["dpo_generator"]
