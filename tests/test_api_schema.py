from jsonschema import validate, ValidationError


EVENT_SCHEMA = {
    "type": "object",
    "required": ["id", "title", "description", "date", "location", "available_seats"],
    "properties": {
        "id": {"type": "integer"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "date": {"type": "string"},
        "location": {"type": "string"},
        "available_seats": {"type": "integer"},
        "category": {"type": "string"},
        "image_url": {"type": "string"},
    },
}


def test_api_events_schema(client):
    resp = client.get("/api/events")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)

    for item in data:
        try:
            validate(instance=item, schema=EVENT_SCHEMA)
        except ValidationError as exc:
            raise AssertionError(f"API /api/events returned invalid schema: {exc}")
