import os
import uuid
import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class SemanticMemory:
    def __init__(self):
        """
        Initializes the local ChromaDB persistent storage and 
        the Google Gemini embedding model.
        """
        # 1. Initialize Chroma local storage (creates a folder called 'cca_chroma')
        self.client = chromadb.PersistentClient(path="./cca_chroma")
        
        # 2. Initialize Google Embeddings (3072 dimensions for gemini-embedding-001)
        # Ensure GOOGLE_API_KEY is in your .env file
        self.embeddings_model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        
        # 3. Create or get the collection
        self.collection = self.client.get_or_create_collection(name="thought_graph")

    def save_thought(self, text: str, metadata: dict = None):
        """
        Embeds a thought using Google API and saves it to ChromaDB.
        Ensures metadata is not empty to satisfy ChromaDB requirements.
        """
        # Generate the mathematical vector (embedding)
        vector = self.embeddings_model.embed_query(text)
        
        # ChromaDB requires at least one key-value pair in metadata
        final_metadata = metadata if metadata and len(metadata) > 0 else {"source": "cca_memory"}
        
        self.collection.add(
            ids=[str(uuid.uuid4())],
            embeddings=[vector],
            documents=[text],
            metadatas=[final_metadata]
        )

    def search_related(self, query: str, limit: int = 3):
        """
        Searches the local database for thoughts semantically related to the query.
        Used for RAG context injection.
        """
        vector = self.embeddings_model.embed_query(query)
        
        results = self.collection.query(
            query_embeddings=[vector],
            n_results=limit
        )
        
        # Flatten the results from Chroma's list-of-lists format
        return results['documents'][0] if results['documents'] else []

    def get_all_thoughts(self):
        """
        Fetches all IDs, documents, metadatas, AND embeddings from the database.
        This is used by the /graph endpoint to calculate intelligent connections.
        """
        return self.collection.get(include=['documents', 'metadatas', 'embeddings'])