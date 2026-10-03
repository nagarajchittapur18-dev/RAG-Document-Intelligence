import pytest
from app.services.chunker import DocumentChunk
from app.services.vector_store import VectorStore


@pytest.fixture
def temp_vector_store(tmp_path):
    chroma_dir = tmp_path / "chroma_test"
    store = VectorStore(
        persist_directory=str(chroma_dir),
        collection_name="test_collection",
    )
    return store


@pytest.fixture
def sample_chunks():
    return [
        DocumentChunk(
            chunk_id="doc_101_p1_c0",
            document_id="101",
            document_name="deep_learning.pdf",
            page_number=1,
            page_chunk_index=0,
            global_chunk_index=0,
            text="Residual connections allow gradients to flow directly through skip connections in deep ResNets.",
            char_count=98,
            word_count=13,
            metadata={"topic": "neural_networks"},
        ),
        DocumentChunk(
            chunk_id="doc_101_p2_c0",
            document_id="101",
            document_name="deep_learning.pdf",
            page_number=2,
            page_chunk_index=0,
            global_chunk_index=1,
            text="Stochastic Gradient Descent with momentum is utilized for training with a learning rate of 0.01.",
            char_count=96,
            word_count=15,
            metadata={"topic": "optimization"},
        ),
        DocumentChunk(
            chunk_id="doc_202_p1_c0",
            document_id="202",
            document_name="biology_plants.pdf",
            page_number=1,
            page_chunk_index=0,
            global_chunk_index=0,
            text="Photosynthesis is the chemical process by which green plants synthesize nutrients from sunlight.",
            char_count=96,
            word_count=12,
            metadata={"topic": "botany"},
        ),
    ]


def test_add_and_count_chunks(temp_vector_store, sample_chunks):
    """Test adding chunks and checking collection count."""
    count = temp_vector_store.add_chunks(sample_chunks)
    assert count == 3
    assert temp_vector_store.collection.count() == 3
    assert temp_vector_store.get_document_chunk_count("101") == 2
    assert temp_vector_store.get_document_chunk_count("202") == 1


def test_similarity_search_retrieval(temp_vector_store, sample_chunks):
    """Test semantic query retrieval finds the most relevant chunk."""
    temp_vector_store.add_chunks(sample_chunks)

    # Query about ResNet skip connections
    results = temp_vector_store.similarity_search(
        query_text="How do skip connections help deep networks train?",
        top_k=2,
    )

    assert len(results) > 0
    top_result = results[0]
    assert top_result.document_id == "101"
    assert top_result.page_number == 1
    assert "Residual connections" in top_result.text
    assert top_result.similarity_score > 0.45


def test_metadata_filtering_single_document(temp_vector_store, sample_chunks):
    """Test filtering search exclusively to a specific document."""
    temp_vector_store.add_chunks(sample_chunks)

    # Query for general concepts but restrict to biology_plants.pdf (doc 202)
    results = temp_vector_store.similarity_search(
        query_text="gradient descent and neural networks",
        top_k=5,
        document_ids=["202"],
    )

    assert len(results) == 1
    assert results[0].document_id == "202"
    assert results[0].document_name == "biology_plants.pdf"


def test_metadata_filtering_multi_document(temp_vector_store, sample_chunks):
    """Test querying across multiple selected documents."""
    temp_vector_store.add_chunks(sample_chunks)

    results = temp_vector_store.similarity_search(
        query_text="scientific methods and processes",
        top_k=5,
        document_ids=["101", "202"],
    )

    retrieved_doc_ids = {r.document_id for r in results}
    assert "101" in retrieved_doc_ids or "202" in retrieved_doc_ids


def test_delete_document_cascade(temp_vector_store, sample_chunks):
    """Test that deleting a document removes all its chunks from the vector database."""
    temp_vector_store.add_chunks(sample_chunks)
    assert temp_vector_store.collection.count() == 3

    # Delete doc 101 (has 2 chunks)
    deleted_count = temp_vector_store.delete_document("101")
    assert deleted_count == 2
    assert temp_vector_store.collection.count() == 1
    assert temp_vector_store.get_document_chunk_count("101") == 0
    assert temp_vector_store.get_document_chunk_count("202") == 1


def test_min_similarity_threshold_filtering(temp_vector_store, sample_chunks):
    """Test that chunks below min_similarity are filtered out."""
    temp_vector_store.add_chunks(sample_chunks)

    # Query completely irrelevant topic with high threshold
    results = temp_vector_store.similarity_search(
        query_text="ancient Roman architectural arches and stone aqueducts",
        top_k=3,
        min_similarity=0.85,  # Very strict threshold
    )

    # All chunks should be rejected as irrelevant
    assert len(results) == 0
