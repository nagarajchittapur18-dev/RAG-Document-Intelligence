import numpy as np
import pytest
from app.services.embedding_service import EmbeddingService


@pytest.fixture
def embedding_service():
    return EmbeddingService()


def test_embedding_service_singleton(embedding_service):
    """Verify that EmbeddingService acts as a singleton to prevent repeated model loading."""
    second_instance = EmbeddingService()
    assert embedding_service is second_instance
    assert embedding_service.model is second_instance.model


def test_embedding_dimension_and_normalization(embedding_service):
    """Verify 384-d output vector and L2 unit-norm property."""
    text = "Retrieval-Augmented Generation enhances generative AI using grounded documents."
    vector = embedding_service.embed_text(text)

    assert isinstance(vector, list)
    assert len(vector) == 384

    # Check L2 unit-norm: ||v||_2 ≈ 1.0
    norm = np.linalg.norm(np.array(vector))
    assert pytest.approx(norm, abs=1e-4) == 1.0


def test_semantic_similarity_order(embedding_service):
    """Verify that semantically related texts have higher cosine similarity than unrelated texts."""
    v_ai = np.array(embedding_service.embed_query("deep neural networks and transformer architecture"))
    v_similar = np.array(embedding_service.embed_query("convolutional neural nets and attention models in machine learning"))
    v_unrelated = np.array(embedding_service.embed_query("traditional recipe for baking chocolate chip cookies"))

    sim_related = float(np.dot(v_ai, v_similar))
    sim_unrelated = float(np.dot(v_ai, v_unrelated))

    assert sim_related > sim_unrelated
    assert sim_related > 0.45
    assert sim_unrelated < 0.25


def test_batch_embedding_matches_single(embedding_service):
    """Verify that batch embedding produces identical vectors to single embedding."""
    texts = [
        "First academic research paper snippet.",
        "Second machine learning benchmark comparison.",
    ]
    batch_vectors = embedding_service.embed_texts(texts)
    single_v0 = embedding_service.embed_text(texts[0])
    single_v1 = embedding_service.embed_text(texts[1])

    assert len(batch_vectors) == 2
    assert np.allclose(batch_vectors[0], single_v0, atol=1e-5)
    assert np.allclose(batch_vectors[1], single_v1, atol=1e-5)
