from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import StreamingHttpResponse
from django.db import transaction
from uuid import uuid4
from core.models import LoggerService
from app.chatbot.models import ChatbotSession, ChatbotMessage
from app.chatbot.serializers import ChatbotMessageSerializer, ChatbotSessionSerializer
from app.products.models import Product, Brand, ProductCategory
from services.openai_service import OpenAIService
from drf_spectacular.utils import extend_schema
import time
from core.renderers import EventStreamRenderer

@extend_schema(tags=['ChatInteraction'])
class ChatInteractionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def _get_product_context(self):
        products = Product.objects.filter(active=True)[:30]
        brands = Brand.objects.filter(active=True)
        categories = ProductCategory.objects.filter(active=True)
        
        context = "Información del catálogo:\n"
        
        context += "Categorías disponibles: "
        context += ", ".join([cat.name for cat in categories])
        context += "\n"
        
        context += "Marcas disponibles: "
        context += ", ".join([brand.name for brand in brands])
        context += "\n"
        
        context += "Productos seleccionados:\n"
        for product in products:
            context += f"- {product.name} (Marca: {product.brand.name}, Categoría: {product.category.name if product.category else 'N/A'})\n"
            context += f"  Precio: ${product.price_usd} USD / {product.price_bs} Bs\n"
            if product.average_rating:
                context += f"  Calificación: {product.average_rating}/5 ({product.total_reviews} reseñas)\n"
            
        return context
    
    @extend_schema(
        request={'application/json': {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'session_token': {'type': 'string'}
            },
            'required': ['message']
        }},
        responses={200: {"type": "string", "format": "text/event-stream"}}
    )
    @action(detail=False, methods=['post'], renderer_classes=[EventStreamRenderer])
    def send_message(self, request):
        try:
            message_text = request.data.get('message')
            session_token = request.data.get('session_token')
            
            if not message_text:
                return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                if session_token:
                    try:
                        session = ChatbotSession.objects.get(
                            session_token=session_token, 
                            active=True
                        )
                    except ChatbotSession.DoesNotExist:
                        session = ChatbotSession.objects.create(
                            user=request.user,
                            session_token=str(uuid4()),
                            active=True
                        )
                        LoggerService.objects.create(
                            user=request.user,
                            action='CREATE',
                            table_name='ChatbotSession',
                            description=f'Created new chatbot session {session.id}'
                        )
                else:
                    session = ChatbotSession.objects.create(
                        user=request.user,
                        session_token=str(uuid4()),
                        active=True
                    )
                    LoggerService.objects.create(
                        user=request.user,
                        action='CREATE',
                        table_name='ChatbotSession',
                        description=f'Created new chatbot session {session.id}'
                    )
                
                user_message = ChatbotMessage.objects.create(
                    session=session,
                    sender='user',
                    message=message_text
                )
                
                LoggerService.objects.create(
                    user=request.user,
                    action='CREATE',
                    table_name='ChatbotMessage',
                    description=f'Created user message {user_message.id}'
                )
                
                bot_message = ChatbotMessage.objects.create(
                    session=session,
                    sender='bot',
                    message=""
                )
                
                LoggerService.objects.create(
                    user=request.user,
                    action='CREATE',
                    table_name='ChatbotMessage',
                    description=f'Created bot message placeholder {bot_message.id}'
                )
            
            previous_messages = ChatbotMessage.objects.filter(
                session=session,
                id__lt=bot_message.id
            ).order_by('created_at')
            
            formatted_messages = []
            
            catalog_context = self._get_product_context()
            system_message = (
    "Eres un asistente útil para la plataforma de comercio electrónico FICCT. "
    "Responde a las consultas de los usuarios sobre productos, pedidos, envíos y gestión de cuentas. "
    "Usa formato Markdown para estructurar tus respuestas, incluyendo:\n"
    "- **Negritas** para términos importantes\n"
    "- Listas con viñetas para enumerar opciones o características\n"
    "No uses tablas o encabezados, solo los elementos mencionados.\n\n"
    "Aquí tienes información sobre nuestro catálogo actual que puedes usar para responder preguntas:\n\n"
    f"{catalog_context}"
)
            
            formatted_messages.append({
                "role": "system",
                "content": system_message
            })
            
            for msg in previous_messages:
                role = "user" if msg.sender == "user" else "assistant"
                formatted_messages.append({
                    "role": role,
                    "content": msg.message
                })
            
            openai_service = OpenAIService()
            stream = openai_service.stream_api(formatted_messages)
            
            response = StreamingHttpResponse(
                self._stream_response_generator(stream, bot_message, request.user),
                content_type='text/event-stream'
            )
            
            response['Cache-Control'] = 'no-cache'
            response['X-Accel-Buffering'] = 'no'
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Credentials'] = 'true'
            
            response['Session-Token'] = session.session_token
            response['Session-Id'] = str(session.id)
            response['Bot-Message-Id'] = str(bot_message.id)
            response['Access-Control-Expose-Headers'] = 'Session-Token,Session-Id,Bot-Message-Id'
            
            return response
            
        except Exception as e:
            LoggerService.objects.create(
                user=request.user,
                action='ERROR',
                table_name='ChatInteraction',
                description=f'Error in send_message streaming: {str(e)}'
            )
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _stream_response_generator(self, stream, bot_message, user):
        """
        Stream generator that yields chunks from OpenAI and updates the message in the database
        when finished.
        """
        complete_response = ""
        try:
            yield "data: \n\n"
            
            for chunk in stream:
                if chunk.choices and hasattr(chunk.choices[0].delta, "content"):
                    content = chunk.choices[0].delta.content
                    if content:
                        complete_response += content
                        yield f"data: {content}\n\n"
            
            bot_message.message = complete_response
            bot_message.save()
            
            LoggerService.objects.create(
                user=user,
                action='UPDATE',
                table_name='ChatbotMessage',
                description=f'Updated bot message {bot_message.id} with streaming response'
            )
            
            yield f"event: complete\ndata: true\n\n"
            
        except Exception as e:
            LoggerService.objects.create(
                user=user,
                action='ERROR',
                table_name='ChatbotMessage',
                description=f'Error in streaming response: {str(e)}'
            )
            yield f"event: error\ndata: {str(e)}\n\n"

