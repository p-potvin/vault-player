"""
VaultWares Agents — specialized agent implementations.

All agents inherit from ExtrovertAgent and implement domain-specific
task handling. They connect to Redis and participate in the
LonelyManager heartbeat & dispatch network.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

__all__ = []

try:
    from agents.text_agent import TextAgent
    __all__.append("TextAgent")
except ImportError:
    pass

try:
    from agents.image_agent import ImageAgent
    __all__.append("ImageAgent")
except ImportError:
    pass

try:
    from agents.video_agent import VideoAgent
    __all__.append("VideoAgent")
except ImportError:
    pass

try:
    from agents.workflow_agent import WorkflowAgent
    __all__.append("WorkflowAgent")
except ImportError:
    pass

try:
    from agents.security_agent import SecurityAgent
    __all__.append("SecurityAgent")
except ImportError:
    pass
