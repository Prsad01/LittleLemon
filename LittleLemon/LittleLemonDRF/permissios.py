from rest_framework.permissions import BasePermission

class IsManager(BasePermission):
    def has_permission(self, request, view):  
        # print("printing from persmisson") 
        # print(bool(request.user.groups.filter(name='Manager').exists() and request.user.is_authenticated)) 
        # print(not bool(request.user.groups.filter(name='Manager').exists() and request.user.is_authenticated)) 
        return bool(request.user.groups.filter(name='Manager').exists() and request.user.is_authenticated)
    
class IsDeliveryCrew(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.groups.filter(name='Delivery-Crew').exists() and request.user.is_authenticated)

#         return super().has_permission(request, view)


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
           return not (bool(request.user.groups.filter(name='Delivery-Crew').exists()) or  bool(request.user.groups.filter(name='Manager').exists()))
        
class NoPermission(BasePermission):
    def has_permission(self, request, view):
        return False