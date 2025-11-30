from server.ai.model import AISuggester

def test_model_init():
    ai = AISuggester()
    assert ai.api_key is not None
    assert ai.model_name is not None
