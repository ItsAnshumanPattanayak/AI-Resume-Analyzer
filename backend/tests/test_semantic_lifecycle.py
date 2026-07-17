import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pytest

from app import semantic
from app.config import settings


class FakeModel:
    def __init__(self) -> None:
        self.encode_calls = 0

    def encode(self, texts, **kwargs):
        del kwargs
        self.encode_calls += 1
        return np.asarray(
            [[float(len(text)), 1.0] for text in texts],
            dtype=np.float32,
        )


@pytest.fixture(autouse=True)
def clear_semantic_state():
    semantic.reset_semantic_state()
    yield
    semantic.reset_semantic_state()


def test_model_loading_is_lazy_and_singleton(monkeypatch) -> None:
    constructions = []

    def build_model(*args, **kwargs):
        constructions.append((args, kwargs))
        return FakeModel()

    monkeypatch.setattr(semantic, "SentenceTransformer", build_model)

    assert constructions == []
    first = semantic.get_semantic_model()
    second = semantic.get_semantic_model()

    assert first is second
    assert len(constructions) == 1


def test_concurrent_first_load_constructs_once(monkeypatch) -> None:
    construction_count = 0

    def build_model(*args, **kwargs):
        nonlocal construction_count
        del args, kwargs
        construction_count += 1
        time.sleep(0.02)
        return FakeModel()

    monkeypatch.setattr(semantic, "SentenceTransformer", build_model)

    with ThreadPoolExecutor(max_workers=8) as executor:
        models = list(executor.map(lambda _: semantic.get_semantic_model(), range(8)))

    assert construction_count == 1
    assert all(model is models[0] for model in models)


def test_failed_initialization_returns_safe_error(monkeypatch) -> None:
    def fail(*args, **kwargs):
        del args, kwargs
        raise OSError("/private/model/path")

    monkeypatch.setattr(semantic, "SentenceTransformer", fail)

    with pytest.raises(RuntimeError) as error:
        semantic.get_semantic_model()

    assert str(error.value) == "The semantic analysis service is unavailable."
    assert "/private/model/path" not in str(error.value)


def test_embedding_cache_hits_and_is_bounded(monkeypatch) -> None:
    model = FakeModel()
    monkeypatch.setattr(semantic, "SentenceTransformer", lambda *args, **kwargs: model)
    monkeypatch.setattr(settings, "semantic_result_cache_size", 2)

    first = semantic.encode_texts(["Python developer"])
    second = semantic.encode_texts(["Python developer"])

    assert np.array_equal(first, second)
    assert model.encode_calls == 1

    semantic.encode_texts(["SQL developer"])
    semantic.encode_texts(["Docker engineer"])
    assert semantic.semantic_cache_size() == 2

    semantic.encode_texts(["Python developer"])
    assert model.encode_calls == 4


def test_embedding_cache_can_be_disabled(monkeypatch) -> None:
    model = FakeModel()
    monkeypatch.setattr(semantic, "SentenceTransformer", lambda *args, **kwargs: model)
    monkeypatch.setattr(settings, "semantic_result_cache_size", 0)

    semantic.encode_texts(["same input"])
    semantic.encode_texts(["same input"])

    assert model.encode_calls == 2
    assert semantic.semantic_cache_size() == 0
