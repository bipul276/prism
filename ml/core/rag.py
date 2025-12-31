import chromadb
from sentence_transformers import SentenceTransformer
import os

class EvidenceRetriever:
    def __init__(self, collection_name="claims"):
        # Connect to Chroma
        host = os.getenv("CHROMA_HOST", "127.0.0.1") # Default to local info, docker-compose uses 'chromadb'
        port = int(os.getenv("CHROMA_PORT", 8000)) # Default 8000
        
        try:
            print(f"Connecting to ChromaDB at {host}:{port}...")
            self.client = chromadb.HttpClient(host=host, port=port)
            self.collection = self.client.get_or_create_collection(name=collection_name)
        except Exception as e:
            print(f"FAILED to connect to ChromaDB: {e}")
            self.client = None
            self.collection = None
        
        # Load embedding model
        # using all-MiniLM-L6-v2 for speed and good performance
        self.device = "cuda" if os.getenv("CUDA_VISIBLE_DEVICES") != "" else "cpu" 
        # Better check:
        import torch
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"RAG Retriever loaded on {self.device}")
        
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device=self.device)

    def retrieve(self, query, n_results=50):
        # Embed query
        query_embedding = self.embedding_model.encode(query).tolist()
        
        if not self.collection:
            print("ChromaDB collection not available.")
            return []

        # Query Chroma
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        evidence = []
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i] if results['metadatas'] else {}
                evidence.append({
                    "text": doc,
                    "url": meta.get("source_url"),
                    "score": results['distances'][0][i] if results['distances'] else 0
                })
        
        return evidence
