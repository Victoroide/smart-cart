from rest_framework import permissions

class DeliveryAssignmentPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
        
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
            
        if request.user.role == 'delivery':
            return obj.delivery_person.id == request.user.id
            
        if request.user.role == 'customer':
            return obj.delivery.order.user.id == request.user.id
            
        return False