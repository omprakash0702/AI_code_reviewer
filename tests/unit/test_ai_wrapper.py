from server.ai.model import AISuggester

class FakeResponse:
    def __init__(self, text):
        self.text = text

    def json(self):
        return {"choices": [{"message": {"content": self.text}}]}

def fake_post(*args, **kwargs):
    return FakeResponse('{"issues":[],"patch":""}')


def test_ai_json_output(monkeypatch):
    def fake_post(*args, **kwargs):
        return FakeResponse('{"issues":[],"patch":""}')

    monkeypatch.setattr("httpx.post", fake_post)

    ai = AISuggester()
    result = ai.generate_review("a.py", "print('hi')", {})
    assert "issues" in result
    assert "patch" in result
