from collections import OrderedDict
from rest_framework import serializers
from .models import Category , Cart, MenuItem, OrderItem ,Order
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator , UniqueTogetherValidator
import datetime

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username','first_name','last_name','email','last_login','is_active','date_joined','password']
        extra_kwargs ={
            'id':{'read_only':True},
            'password':{'write_only':True,'required':True},
        }

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        if(self.context.get('Role') == 'Manager'):
            user.groups.add(1)
        elif (self.context.get('Role') == 'Delivery-Crew'):
             user.groups.add(2)   
        else:
            pass
        user.set_password(validated_data.pop("password"))
        user.save()
        return user

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields =['id','slug','title']
        extra_kwargs ={
            'id':{'read_only':True},
            'title':{'validators':[ UniqueValidator(queryset=Category.objects.all(),message='category already exists',)]}
        }
        
class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only = True)
    category_id = serializers.IntegerField(write_only=True)
    class Meta:
        model = MenuItem
        fields = ['id','title','price','featured','category','category_id']
        extra_kwargs = {
            'id':{'read_only':True},
        }
        validators = [
            UniqueTogetherValidator(
                queryset=MenuItem.objects.select_related('category').all(),
                fields=('title','category_id'),
                message='Title alredy exists with category'
            )
            ]
        
class CartSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only = True)
    menuItem = MenuItemSerializer(read_only = True)
    # user_id = serializers.IntegerField(write_only=True)
    menuItem_id = serializers.IntegerField(write_only=True)
    # price_after_tax = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ('id','user','menuItem','menuItem_id','quantity','unite_price','price')
        extra_kwargs ={
            'id':{'read_only':True},
            'price':{'read_only':True},
            'unite_price':{'read_only':True},

            }

        # validators = [
        #     UniqueTogetherValidator(
        #         queryset = Cart.objects.select_related('menuItem','user').all(),
        #         fields = ('menuItem_id','user_id'),
        #         message ='Item alredy exits'
        #     )]

    def create(self, validated_data):
        quantity = validated_data.pop('quantity')
        menuItem_id = validated_data.pop('menuItem_id')
        unite_price = MenuItem.objects.filter(pk=menuItem_id).values('price').get().get('price')
        user = self.context['user'].id
        price = quantity * unite_price

        
        cart = Cart.objects.create(
            user=User.objects.get(pk=user),
            quantity=quantity,
            menuItem= MenuItem.objects.get(pk=menuItem_id),
            price=price,
            unite_price=unite_price
            )
        cart.save()
        return cart

class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    delivery_crew = UserSerializer(read_only=True)
    class Meta:
        model = Order
        fields = ['id','user','delivery_crew','status','total','date']
        extra_kwargs = {
            'id':{'read_only':True},
            'user':{'read_only':True},
            'total':{'read_only':True},
            'date':{'read_only':True},
            # 'delivery_crew':{'read_only':True},
        }

    def create(self, validated_data):
        cart_items = Cart.objects.filter(user=self.context['user'])
        if (cart_items.count() == 0):
            raise serializers.ValidationError({'details':'Your Cart is empty! Please add items in cart'})
        else:
            total = 0
            for item in cart_items:
                total+= item.price
            order = Order.objects.create(
                    user=self.context['user'],
                    total=total,
                    status=0,
                )
            return order
        return super().create(validated_data)
       
class OrderItemSerializer(serializers.ModelSerializer):
    # cart_id= serializers.IntegerField(write_only=True)
    menuItem = MenuItemSerializer(read_only=True)
    order = OrderSerializer(read_only=True)
    class Meta:
        model = OrderItem
        fields = fields = ('id','order','menuItem','quantity','unite_price','price')
        extra_kwargs = {
            'id':{'read_only':True},
            'order':{'read_only':True},
            'menuItem':{'read_only':True},
            'quantity':{'read_only':True},
            'unite_price':{'read_only':True},
            'price':{'read_only':True},
        }


    # def to_representation(self, instance):
    #     customer_data = super().to_representation(instance)
    #     customer_data['User'] =  customer_data.pop('order')
    #     return customer_data
    #     return super().to_representation(instance)

    def create(self, validated_data):
        print("from order item serializer")
        cart_items = Cart.objects.filter(user=self.context['user'])
        
        for cart_item in cart_items:
            order_item = OrderItem.objects.create(
            order_id = self.context['order_id'],
            menuItem = cart_item.menuItem,
            quantity=cart_item.quantity,
            unite_price=cart_item.unite_price,
            price = cart_item.price
            )
            cart_item.delete()
        return order_item
        
       