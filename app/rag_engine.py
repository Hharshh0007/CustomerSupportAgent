import json
import os
import pickle
from typing import List, Dict, Any, Tuple
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

class RAGEngine:
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2", index_path: str = "data/faiss_index.bin"):
        self.embedding_model = embedding_model
        self.index_path = index_path
        self.model = SentenceTransformer(embedding_model)
        self.index = None
        self.faqs = []
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
        
    def load_faqs(self, faq_path: str = "data/faqs.json") -> List[Dict[str, Any]]:
        """Load FAQ data from JSON file"""
        try:
            with open(faq_path, 'r', encoding='utf-8') as f:
                self.faqs = json.load(f)
            print(f"Loaded {len(self.faqs)} FAQs from {faq_path}")
            return self.faqs
        except FileNotFoundError:
            print(f"FAQ file not found: {faq_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parsing FAQ JSON: {e}")
            return []
    
    def load_order_data(self, order_path: str = "data/order_database.json") -> List[Dict[str, Any]]:
        """Load order data and convert to FAQ format for RAG"""
        try:
            with open(order_path, 'r', encoding='utf-8') as f:
                orders = json.load(f)
            
            # Convert orders to FAQ format for better RAG retrieval
            order_faqs = []
            for order in orders:
                items_text = ", ".join([f"{item['name']} (x{item['quantity']})" for item in order['items']])
                
                order_faqs.append({
                    "question": f"Order {order['order_id']} details",
                    "answer": f"Order ID: {order['order_id']}, Customer: {order['customer_name']}, Restaurant: {order['restaurant']}, Items: {items_text}, Total: ${order['total_amount']}, Status: {order['status']}, Delivery Address: {order['delivery_address']}",
                    "category": "order_data",
                    "order_id": order['order_id']
                })
            
            print(f"Loaded {len(order_faqs)} order records for RAG")
            return order_faqs
        except FileNotFoundError:
            print(f"Order database not found: {order_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parsing order JSON: {e}")
            return []
    
    def create_embeddings(self) -> np.ndarray:
        """Create embeddings for all FAQ questions and answers"""
        if not self.faqs:
            self.load_faqs()
        
        # Load order data and add to FAQs
        order_faqs = self.load_order_data()
        self.faqs.extend(order_faqs)
        
        # Combine question and answer for better context
        texts = []
        for faq in self.faqs:
            combined_text = f"{faq['question']} {faq['answer']}"
            texts.append(combined_text)
        
        print(f"Creating embeddings for {len(texts)} entries (FAQs + Orders)...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        print(f"Created embeddings with shape: {embeddings.shape}")
        return embeddings
    
    def build_index(self) -> faiss.Index:
        """Build FAISS index from embeddings"""
        embeddings = self.create_embeddings()
        
        # Create FAISS index
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add embeddings to index
        self.index.add(embeddings.astype('float32'))
        
        print(f"Built FAISS index with {self.index.ntotal} vectors")
        return self.index
    
    def save_index(self):
        """Save FAISS index and FAQ data to disk"""
        if self.index is None:
            print("No index to save. Build index first.")
            return
        
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        faiss.write_index(self.index, self.index_path)
        
        # Save FAQ data alongside index
        faq_data_path = self.index_path.replace('.bin', '_faqs.pkl')
        with open(faq_data_path, 'wb') as f:
            pickle.dump(self.faqs, f)
        
        print(f"Saved index to {self.index_path} and FAQ data to {faq_data_path}")
    
    def load_index(self) -> bool:
        """Load FAISS index and FAQ data from disk"""
        try:
            self.index = faiss.read_index(self.index_path)
            
            # Load FAQ data
            faq_data_path = self.index_path.replace('.bin', '_faqs.pkl')
            with open(faq_data_path, 'rb') as f:
                self.faqs = pickle.load(f)
            
            print(f"Loaded index with {self.index.ntotal} vectors and {len(self.faqs)} FAQs")
            return True
        except FileNotFoundError:
            print(f"Index file not found: {self.index_path}")
            return False
        except Exception as e:
            print(f"Error loading index: {e}")
            return False
    
    def search(self, query: str, k: int = 3) -> List[Tuple[Dict[str, Any], float]]:
        """Search for relevant FAQs using semantic similarity"""
        if self.index is None:
            if not self.load_index():
                print("Building new index...")
                self.build_index()
                self.save_index()
        
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search index
        scores, indices = self.index.search(query_embedding.astype('float32'), k)
        
        # Return results with scores
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.faqs):
                results.append((self.faqs[idx], float(score)))
        
        return results
    
    def get_relevant_faqs(self, query: str, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Get FAQs above similarity threshold"""
        results = self.search(query, k=5)
        relevant_faqs = []
        
        for faq, score in results:
            if score >= threshold:
                faq_with_score = faq.copy()
                faq_with_score['similarity_score'] = score
                relevant_faqs.append(faq_with_score)
        
        return relevant_faqs
    
    def initialize(self):
        """Initialize RAG engine - load existing index or build new one"""
        if not self.load_index():
            print("Building new RAG index...")
            self.build_index()
            self.save_index()
        print("RAG engine initialized successfully!")

rag_engine = RAGEngine()

def get_rag_engine() -> RAGEngine:
    """Get the global RAG engine instance"""
    return rag_engine
