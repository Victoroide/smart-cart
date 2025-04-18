from .pinecone_service import PineconeService
from app.products.serializers import ProductSerializer
from app.products.models import Product

class RecommendationService:
    def __init__(self):
        self.pinecone_service = PineconeService()
    
    def get_similar_products(self, product_name, description="", top_k=5):
        query_text = f"{product_name} {description}"
        metadata_filter = {"active": True}
        results = self.pinecone_service.search_similar_products(query_text, top_k, metadata_filter=metadata_filter)
        
        if results:
            similar_products = []
            for match in results.matches:
                product_data = match.metadata
                product_data['score'] = match.score
                product_data['vector_id'] = match.id
                similar_products.append(product_data)
            
            return similar_products
        
        return []
    
    def get_recommendations_by_user_history(self, product_ids, top_k=5):
        from app.products.models import Product
        
        products = Product.objects.filter(id__in=product_ids)
        
        combined_text = " ".join([f"{p.name} {p.description or ''}" for p in products])
        
        return self.get_similar_products(combined_text, top_k=top_k)
        
    def get_product_recommendations(self, user_id, max_results=5):
        from app.orders.models import OrderItem
        from app.products.models import Product
        
        recent_orders = OrderItem.objects.filter(
            order__user_id=user_id
        ).values_list('product_id', flat=True).distinct()[:10]
        
        if not recent_orders:
            return []
            
        return self.get_recommendations_by_user_history(recent_orders, top_k=max_results)