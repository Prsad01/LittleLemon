from django.urls import path,include
from .views import CategoryView,MenuItemview,UserManagerView,UserDelivery_CrewView,CartView,OrderItemView
from rest_framework.routers import DefaultRouter

router = DefaultRouter(trailing_slash=False)
# router.register('category',CategoryView,basename='category')
router.register('menue-item',MenuItemview,basename='menue-item')
router.register('groups/manager/users',UserManagerView,basename='manager')
router.register('groups/delivery-crew/users',UserDelivery_CrewView,basename='delivery-crew')
router.register('cart/menu-items',CartView,basename='cart')
router.register('orders',OrderItemView,basename='orders')

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    
    
]+router.urls