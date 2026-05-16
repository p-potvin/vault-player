"""
VaultWares Agents — specialized agent implementations.

All agents inherit from ExtrovertAgent and implement domain-specific
task handling. They connect to Redis and participate in the
LonelyManager heartbeat & dispatch network.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from agents.text_agent import TextAgent
except ImportError:
    TextAgent = None

try:
    from agents.image_agent import ImageAgent
except ImportError:
    ImageAgent = None

try:
    from agents.video_agent import VideoAgent
except ImportError:
    VideoAgent = None

try:
    from agents.workflow_agent import WorkflowAgent
except ImportError:
    WorkflowAgent = None

try:
    from agents.security_agent import SecurityAgent
except ImportError:
    SecurityAgent = None

__all__ = [name for name, val in [
    ("TextAgent", TextAgent),
    ("ImageAgent", ImageAgent),
    ("VideoAgent", VideoAgent),
    ("WorkflowAgent", WorkflowAgent),
    ("SecurityAgent", SecurityAgent)
] if val is not None]
