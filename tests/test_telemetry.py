from app.telemetry import init_telemetry, get_tracer


def test_opentelemetry_tracer_initialization():
    tracer = init_telemetry("test-service")
    assert tracer is not None

    t2 = get_tracer()
    assert t2 is not None


def test_opentelemetry_span_creation():
    tracer = get_tracer()
    with tracer.start_as_current_span("unit_test_span") as span:
        span.set_attribute("test_key", "test_val")
        assert span.is_recording()
