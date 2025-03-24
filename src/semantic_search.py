import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class SemanticSearch:
    def __init__(self):
        """Initializes the embeddings model and FAISS index"""
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.index = None
        self.texts = []
        self.metadata = []

    def add_texts(self, texts: List[str], metadata: List[Dict] = None):
        """
        Adds texts to the search index.
        
        Args:
            texts: List of texts to index
            metadata: List of metadata associated with each text
        """
        try:
            # Generate embeddings
            embeddings = self.model.encode(texts, convert_to_tensor=True)
            embeddings_np = embeddings.cpu().numpy()

            # Create or update FAISS index
            if self.index is None:
                dimension = embeddings_np.shape[1]
                self.index = faiss.IndexFlatL2(dimension)
            
            # Add embeddings to index
            self.index.add(embeddings_np)
            
            # Save texts and metadata
            start_idx = len(self.texts)
            self.texts.extend(texts)
            if metadata:
                self.metadata.extend(metadata)
            else:
                self.metadata.extend([{} for _ in texts])
            
            logger.info(f"Added {len(texts)} texts to semantic index")
            
        except Exception as e:
            logger.error(f"Error adding texts to index: {e}")
            raise

    def search(self, query: str, k: int = 5) -> List[Tuple[str, Dict, float]]:
        """
        Searches for texts most similar to the query.
        
        Args:
            query: Query text
            k: Number of results to return
            
        Returns:
            List of tuples (text, metadata, score)
        """
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query], convert_to_tensor=True)
            query_embedding_np = query_embedding.cpu().numpy()
            
            # Perform search
            if self.index is None or len(self.texts) == 0:
                return []
            
            k = min(k, len(self.texts))
            distances, indices = self.index.search(query_embedding_np, k)
            
            # Format results
            results = []
            for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self.texts):  # Verify valid index
                    score = 1 / (1 + dist)  # Convert distance to similarity score
                    results.append((self.texts[idx], self.metadata[idx], score))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []

    def clear(self):
        """Clears the index and stored texts"""
        self.index = None
        self.texts = []
        self.metadata = [] 