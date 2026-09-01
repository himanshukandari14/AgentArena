import logging
import sys
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger(__name__)

_initialized = False


def init_telemetry(service_name: str = "agent-forge") -> trace.Tracer:
    """Initializes OpenTelemetry TracerProvider with Service Resource attributes."""
    global _initialized
    if not _initialized:
        resource = Resource.create({"service.name": service_name, "environment": "evaluation"})
        provider = TracerProvider(resource=resource)
        
        # Add Simple span processor for immediate span exports
        processor = SimpleSpanProcessor(ConsoleSpanExporter(out=sys.stdout))
        provider.add_span_processor(processor)
        
        trace.set_tracer_provider(provider)
        _initialized = True
        logger.info("OpenTelemetry instrumentation initialized.")

    return trace.get_tracer("agentarena.tracer")


def get_tracer() -> trace.Tracer:
    """Get active OpenTelemetry tracer."""
    return trace.get_tracer("agentarena.tracer")
