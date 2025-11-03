"""
Observability module with tracing
"""
from .otel import init_tracing

__all__ = [
    "init_tracing"
]
