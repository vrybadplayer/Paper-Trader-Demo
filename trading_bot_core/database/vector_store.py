"""
Vector Store - ChromaDB Persistent Client
In-process embedded HNSW cosine index updated continuously after each trade.
Provides dynamic RAG (Retrieval-Augmented Generation) capabilities for market psychology and regime analysis.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logging.warning("ChromaDB not available. Vector store functionality will be limited.")

from ..models.schemas import PortfolioState

class VectorStore:
    """
    Embedded ChromaDB vector store for storing and retrieving market knowledge, 
    trade memories, and regime information.
    Uses HNSW index for fast cosine similarity search.
    """
    
    def __init__(self, persist_directory: str = "database/data/chroma_db", 
                 collection_name: str = "trading_memory"):
        """
        Initialize the vector store.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name of the collection to use
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.logger = logging.getLogger(__name__)
        
        # Ensure the directory exists
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize ChromaDB if available
        if CHROMADB_AVAILABLE:
            self._initialize_chromadb()
        else:
            self.logger.warning("ChromaDB not available. Using mock vector store.")
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Create persistent client
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                self.logger.info(f"Loaded existing collection: {self.collection_name}")
            except Exception:
                # Collection doesn't exist, create it
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}  # Use cosine similarity
                )
                self.logger.info(f"Created new collection: {self.collection_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize ChromaDB: {e}")
            self.client = None
            self.collection = None
    
    def is_available(self) -> bool:
        """Check if the vector store is available and initialized."""
        return CHROMADB_AVAILABLE and self.client is not None and self.collection is not None
    
    def _generate_id(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """Generate a unique ID for a document based on its content and metadata."""
        # Create a hash of the content and metadata
        hash_input = content
        if metadata:
            hash_input += str(sorted(metadata.items()))
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def add_text(self, text: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Add a text document to the vector store.
        
        Args:
            text: The text content to store
            metadata: Optional metadata dictionary
            
        Returns:
            bool: True if added successfully, False otherwise
        """
        if not self.is_available():
            self.logger.warning("Vector store not available. Skipping add_text.")
            return False
        
        try:
            doc_id = self._generate_id(text, metadata)
            
            # Prepare metadata
            if metadata is None:
                metadata = {}
            
            # Add timestamp if not present
            if "timestamp" not in metadata:
                metadata["timestamp"] = datetime.utcnow().isoformat()
            
            # Add to collection
            self.collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            self.logger.debug(f"Added document to vector store: {doc_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding text to vector store: {e}")
            return False
    
    def add_trade_memory(self, trade_data: Dict[str, Any]) -> bool:
        """
        Add a trade execution to the vector store as memory for future reference.
        
        Args:
            trade_data: Dictionary containing trade information
            
        Returns:
            bool: True if added successfully, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            # Create a text representation of the trade
            text_parts = [
                f"Trade: {trade_data.get('action', '')} {trade_data.get('quantity', 0)} shares of {trade_data.get('ticker', '')}",
                f"Price: ${trade_data.get('execution_price', 0):.2f}",
                f"Timestamp: {trade_data.get('timestamp_utc', '')}",
                f"P&L: ${trade_data.get('realized_pnl', 0):.2f}" if trade_data.get('realized_pnl') else "",
                f"Signal: {trade_data.get('trigger_signal', '')}",
                f"Critic Verdict: {trade_data.get('critic_verdict_ref', '')}"
            ]
            
            # Filter out empty parts
            text = " | ".join([part for part in text_parts if part])
            
            # Prepare metadata
            metadata = {
                "type": "trade",
                "ticker": trade_data.get('ticker', ''),
                "action": trade_data.get('action', ''),
                "timestamp": trade_data.get('timestamp_utc', ''),
                "price": trade_data.get('execution_price', 0),
                "quantity": trade_data.get('quantity', 0)
            }
            
            return self.add_text(text, metadata)
        except Exception as e:
            self.logger.error(f"Error adding trade memory: {e}")
            return False
    
    def query_knowledge(self, query_text: str, n_results: int = 5, 
                       filter_dict: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Query the vector store for relevant knowledge.
        
        Args:
            query_text: The query text to search for
            n_results: Number of results to return
            filter_dict: Optional metadata filter
            
        Returns:
            List of result dictionaries with content, metadata, and similarity scores
        """
        if not self.is_available():
            self.logger.warning("Vector store not available. Returning empty results.")
            return []
        
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=filter_dict
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    result = {
                        "content": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "similarity": results['distances'][0][i] if results['distances'] else 0.0
                    }
                    formatted_results.append(result)
            
            return formatted_results
        except Exception as e:
            self.logger.error(f"Error querying vector store: {e}")
            return []
    
    def query_market_psychology(self, query_text: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Query specifically for market psychology patterns.
        
        Args:
            query_text: The query text
            n_results: Number of results to return
            
        Returns:
            List of market psychology relevant results
        """
        filter_dict = {"type": {"$in": ["market_psychology", "behavior", "sentiment"]}}
        return self.query_knowledge(query_text, n_results, filter_dict)
    
    def query_regime_indicators(self, query_text: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Query specifically for regime indicators and macroeconomic data.
        
        Args:
            query_text: The query text
            n_results: Number of results to return
            
        Returns:
            List of regime indicator relevant results
        """
        filter_dict = {"type": {"$in": ["regime", "macro", "economic"]}}
        return self.query_knowledge(query_text, n_results, filter_dict)
    
    def get_collection_count(self) -> int:
        """Get the number of documents in the collection."""
        if not self.is_available():
            return 0
        try:
            return self.collection.count()
        except Exception as e:
            self.logger.error(f"Error getting collection count: {e}")
            return 0
    
    def reset_collection(self) -> bool:
        """
        Reset the collection (delete all documents).
        Use with caution - primarily for testing.
        
        Returns:
            bool: True if reset successfully, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            # Delete the collection and recreate it
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self.logger.info(f"Reset collection: {self.collection_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error resetting collection: {e}")
            return False

# Example usage (for testing)
if __name__ == "__main__":
    # Initialize vector store
    vs = VectorStore("./test_chroma_db", "test_collection")
    
    if vs.is_available():
        # Add some sample knowledge
        vs.add_text(
            "Retail FOMO behavior occurs when investors rush to buy assets fearing they will miss out on gains, often leading to buying at peak prices.",
            {"type": "market_psychology", "pattern": "FOMO"}
        )
        
        vs.add_text(
            "Whale distribution traps occur when large holders gradually sell into rising prices, luring in retail buyers before a sharp reversal.",
            {"type": "market_psychology", "pattern": "distribution_trap"}
        )
        
        # Query the knowledge
        results = vs.query_knowledge("What is FOMO in trading?", n_results=2)
        print(f"Found {len(results)} results for FOMO query:")
        for result in results:
            print(f"- {result['content'][:100]}... (similarity: {result['similarity']:.3f})")
        
        # Add a trade memory
        trade_data = {
            "action": "BUY",
            "quantity": 100,
            "ticker": "AAPL",
            "execution_price": 150.0,
            "timestamp_utc": "2026-08-21T10:30:00Z",
            "realized_pnl": 0.0,
            "trigger_signal": "momentum_breakout",
            "critic_verdict_ref": "approved_with_conditions"
        }
        vs.add_trade_memory(trade_data)
        
        print(f"Total documents in collection: {vs.get_collection_count()}")
    else:
        print("ChromaDB not available. Install with: pip install chromadb")
    
    # Clean up test directory
    import shutil
    if os.path.exists("./test_chroma_db"):
        shutil.rmtree("./test_chroma_db")