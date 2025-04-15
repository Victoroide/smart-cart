import pinecone
from base import settings
from .openai_service import OpenAIService

class PineconeService:
    def __init__(self, index_name=settings.PINECONE_INDEX_NAME):
        self.api_key = settings.PINECONE_API_KEY
        self.index_name = index_name
        self.namespace = ""
        self.openai_service = OpenAIService()
        
        self.pc = pinecone.Pinecone(api_key=self.api_key)
        self.index = self.pc.Index(self.index_name)
    
    def upsert_product(self, product):
        try:
            text_to_embed = f"{product.name} {product.description or ''} {product.technical_specifications or ''}"
            
            embedding = self.openai_service.get_embeddings(text_to_embed)
            
            if embedding:
                vector_id = str(product.uuid)
                
                metadata = {
                    "name": product.name,
                    "description": product.description or "",
                    "brand_name": product.brand.name,
                    "category_name": product.category.name if product.category else None,
                    "technical_specifications": product.technical_specifications or "",
                    "price_usd": str(product.price_usd) if product.price_usd else None,
                    "price_bs": str(product.price_bs) if product.price_bs else None,
                    "active": product.active
                }
                
                self.index.upsert(
                    vectors=[{
                        "id": vector_id,
                        "values": embedding,
                        "metadata": metadata
                    }],
                    namespace=self.namespace
                )
                
                return True
            else:
                return False
        except Exception as e:
            raise Exception(f"An error occurred during Pinecone upsert: {e}")
    
    def delete_product(self, product_uuid):
        try:
            self.index.delete(ids=[str(product_uuid)], namespace=self.namespace)
            return True
        except Exception as e:
            raise Exception(f"An error occurred during Pinecone delete: {e}")
    
    def search_similar_products(self, query_text, top_k=5, metadata_filter=None):
        try:
            query_embedding = self.openai_service.get_embeddings(query_text)
            
            if query_embedding:
                query_params = {
                    "vector": query_embedding,
                    "top_k": top_k,
                    "include_values": True,
                    "include_metadata": True,
                    "namespace": self.namespace
                }
                
                if metadata_filter:
                    query_params["filter"] = metadata_filter
                
                results = self.index.query(**query_params)
                
                return results
            else:
                return None
        except Exception as e:
            raise Exception(f"An error occurred during Pinecone query: {e}")
        
    def bulk_upsert(self, products):
        try:
            vectors = []
            for product in products:
                text_to_embed = f"{product.name} {product.description or ''} {product.technical_specifications or ''}"
                embedding = self.openai_service.get_embeddings(text_to_embed)
                
                if embedding:
                    vector_id = str(product.uuid)
                    metadata = {
                        "name": product.name,
                        "brand_name": product.brand.name,
                        "category_name": product.category.name if product.category else None,
                        "description": product.description or "",
                        "technical_specifications": product.technical_specifications or "",
                        "price_usd": str(product.price_usd) if product.price_usd else None,
                        "price_bs": str(product.price_bs) if product.price_bs else None,
                    }
                    vectors.append({
                        "id": vector_id,
                        "values": embedding,
                        "metadata": metadata
                    })
            
            if vectors:
                self.index.upsert(vectors=vectors, namespace=self.namespace)
                return True
            return False
        except Exception as e:
            raise Exception(f"An error occurred during bulk upsert: {e}")
    
    def fetch_all_ids(self, namespace=""):
        try:
            zero_vector = [0] * 1536
            response = self.index.query(
                vector=zero_vector, 
                top_k=10000, 
                include_metadata=True, 
                include_values=False, 
                namespace=namespace or self.namespace
            )
            return set(match['id'] for match in response['matches'])
        except Exception as e:
            raise Exception(f"An error occurred during fetching IDs from Pinecone: {e}")