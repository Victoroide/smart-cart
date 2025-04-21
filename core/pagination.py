from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.core.paginator import InvalidPage
from rest_framework.exceptions import NotFound

class CustomPagination(PageNumberPagination):
    page_size = 200
    page_size_query_param = 'page_size'
    max_page_size = 200
    
    def get_paginated_response(self, data):
        return Response({
            'items': data,
            'total': self.page.paginator.count,
            'page': int(self.request.query_params.get('page', 1)),
            'page_size': self.get_page_size(self.request),
            'pages': self.page.paginator.num_pages,
            'has_next': self.page.has_next(),
            'has_prev': self.page.has_previous(),
        })
    
    def paginate_queryset(self, queryset, request, view=None):
        sort_by = request.query_params.get('sort_by')
        sort_order = request.query_params.get('sort_order', 'asc').lower()
        
        if sort_by:
            order_prefix = '-' if sort_order == 'desc' else ''
            queryset = queryset.order_by(f'{order_prefix}{sort_by}')
        
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = self.django_paginator_class(queryset, page_size)
        page_number = request.query_params.get(self.page_query_param, 1)
        
        try:
            self.page = paginator.page(page_number)
        except InvalidPage as exc:
            msg = self.invalid_page_message.format(
                page_number=page_number, message=str(exc)
            )
            raise NotFound(msg)

        if paginator.num_pages > 1 and self.template is not None:
            self.display_page_controls = True

        self.request = request
        return list(self.page)