from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny 
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED , HTTP_200_OK ,HTTP_400_BAD_REQUEST,HTTP_404_NOT_FOUND
from .models import Category, MenuItem , Cart, OrderItem, Order
from .serializers import CategorySerializer, MenuItemSerializer, UserSerializer, CartSerializer, OrderSerializer, OrderItemSerializer
from .permissios import IsManager, IsDeliveryCrew, IsCustomer, NoPermission
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action

class CategoryView(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data,many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data , status=HTTP_201_CREATED)
        return Response(serializer.errors , status=HTTP_400_BAD_REQUEST)

class MenuItemview(viewsets.ModelViewSet):
    queryset = MenuItem.objects.select_related('category').all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsAuthenticated ]
    ordering_fields=['price']
    search_fields=['title','category__title']


    

    def get_permissions(self):
        # if ( self.request.user.groups.filter(name="Delivery-Crew").exists()):
        # print(self.request.user)
        if (self.request.method == 'GET'):
            if (self.request.user.groups.filter(name="Delivery-Crew").exists()):
              
                self.permission_classes = [IsDeliveryCrew]
        else:
            self.permission_classes = [IsManager]
        return [permission() for permission in self.permission_classes]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data,many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data , status=HTTP_201_CREATED)
        return Response(serializer.errors , status=HTTP_400_BAD_REQUEST)

class UserManagerView(viewsets.ModelViewSet):
    queryset = User.objects.filter(groups__name='Manager')
    serializer_class = UserSerializer
    permission_classes = [IsManager]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data,many=True,context={'Role':'Manager'})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data , status=HTTP_201_CREATED)
        return Response(serializer.errors , status=HTTP_400_BAD_REQUEST)
        return Response({'Success':'added'})

class UserDelivery_CrewView(viewsets.ModelViewSet):
    queryset=User.objects.filter(groups__name='Delivery-Crew')
    serializer_class = UserSerializer
    permission_classes = [IsManager]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data,many=True,context={'Role':'Delivery-Crew'})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data , status=HTTP_201_CREATED)
        return Response(serializer.errors , status=HTTP_400_BAD_REQUEST)    

class CartView(viewsets.ModelViewSet):
    queryset = Cart.objects.select_related('user','menuItem').all()
    serializer_class = CartSerializer
    permission_classes = [IsCustomer]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data,many=True,context={'user':request.user})
       
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data , status=HTTP_201_CREATED)
        return Response(serializer.errors)
        return Response({'df':'asdghas'})
    
    def get_queryset(self):
        querset = Cart.objects.select_related('user','menuItem').all().filter(user=self.request.user)
        print(querset.count())
        return querset
    

    @action(url_path='flush',methods=['DELETE'],detail=False , permission_classes=[IsCustomer])
    def flush_cart(self, request, *args, **kwargs):
        self.get_queryset().delete()
        return Response({'details':'All items has been removed'})
        

class OrderView(viewsets.ModelViewSet):
    queryset = Order.objects.select_related('user').all()
    serializer_class = OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = OrderSerializer(data=self.request.data,context={'user':self.request.user})
        if(serializer.is_valid()):
            serializer.save()
            return {'saved':True,'order_details':serializer.data}
        return {'saved':False,'order_errors':serializer.errors}

    # def destroy(self, request, pk,*args, **kwargs):
    #     order = get_object_or_404(Order,pk=pk)
    #     order.delete()
 
class OrderItemView(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [AllowAny]


    def get_permissions(self):
        if self.request.user.groups.filter(name='Delivery-Crew').exists() and self.request.method in ['PATCH','GET']:
            self.permission_classes = [IsDeliveryCrew]

        elif self.request.user.groups.filter(name='Manager').exists() and self.request.method in ['DELETE','GET','PUT','PATCH']  :
                self.permission_classes = [IsManager]

        else:
            if self.request.method in ['GET','POST']:
                self.permission_classes = [IsCustomer]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        if self.request.user.groups.filter(name='Delivery-Crew').exists():
            # self.queryset = OrderItem.objects.select_related('order','menuItem').filter(order__delivery_crew =self.request.user)
            self.queryset = Order.objects.select_related('delivery_crew').filter(delivery_crew=self.request.user)

        elif self.request.user.groups.filter(name='Manager').exists() and self.request.method in ['DELETE','GET']:
            self.queryset = Order.objects.select_related('user','delivery_crew').all()

        else:
            self.queryset = OrderItem.objects.select_related('order','menuItem').filter(order__user =self.request.user)
        return self.queryset

    def retrieve(self, request,pk, *args, **kwargs):
       
        if self.request.user.groups.filter(name='Manager').exists() or self.request.user.groups.filter(name='Delivery-Crew').exists():
            order = get_object_or_404(Order,pk=pk)
            serializer = OrderSerializer(order)

        else:   
            order = get_object_or_404(OrderItem,order=pk)
            serializer = OrderItemSerializer(order)

        return Response(serializer.data)
        
    def list(self, request, *args, **kwargs):
        query = self.get_queryset()
        if self.request.user.groups.filter(name='Delivery-Crew').exists() or self.request.user.groups.filter(name='Manager').exists():
            search = self.request.query_params.get('search')
            if search:
                query=query.filter(delivery_crew__username__icontains=search)

            if self.request.query_params.get('status') == 'pending':
                query = query.filter(status=0)
            if self.request.query_params.get('status') == 'delivered':
                query = query.filter(status=1)
            
            if self.request.query_params.get('ordering') :
                query = query.order_by(self.request.query_params.get('ordering'))
              
            serializer = OrderSerializer(query,many=True)
            return Response(serializer.data)
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        order = OrderView.create(self,request=self.request)
        if(order['saved']==True):
            serializer = self.get_serializer(data= self.request.data, context={'user':request.user,'order_id':order['order_details']['id'] })

            if serializer.is_valid():
                serializer.save()

                return Response(serializer.data)
            else:
                return Response(serializer.errors)
        return Response(order['order_errors'])
    
    def destroy(self, request,pk, *args, **kwargs):
        order = get_object_or_404(Order,pk=pk)
        order.delete()
        return Response({'details':'Item Deleted successfully'})
    
        # order = OrderView.destroy(self, request=self.request,pk=pk, *args, **kwargs)
        # if order:
        #     print("from order item serializer printing order",order)

    def partial_update(self, request, pk,*args, **kwargs):
        data = self.request.data
        order_object = get_object_or_404(Order,pk=pk)
        try:
            if self.request.user.groups.filter(name='Manager').exists():
                User.objects.get(pk = data.get('delivery_crew')).groups.filter(name='Delivery-Crew').exists()
                order_object.delivery_crew_id = data.get('delivery_crew',order_object.delivery_crew_id)
                order_object.status = data.get('status',order_object.status)
                
        
            if self.request.user.groups.filter(name='Delivery-Crew').exists():
                if(order_object.delivery_crew == self.request.user):
                    order_object.status = data.get('status',order_object.status)
                else:
                    return Response({'details':'order is not belongs to you'},status=HTTP_400_BAD_REQUEST)

            order_object.save()
            order_object_serializer = OrderSerializer(order_object)
            return Response(order_object_serializer.data)
        except ObjectDoesNotExist:
            return Response({'details':'Delivery Crew not exists'},status=HTTP_404_NOT_FOUND)
        
        finally:
            order_object.status = data.get('status',order_object.status)
            order_object.save()
            order_object_serializer = OrderSerializer(order_object)
            return Response(order_object_serializer.data)