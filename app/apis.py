from app import application
from flask import jsonify, Response, session
from app.models import *
from app import *
import uuid
from datetime import datetime
from marshmallow import Schema, fields
from flask_restful import Resource, Api
from flask_apispec.views import MethodResource
from flask_apispec import marshal_with, doc, use_kwargs
from sqlalchemy import text
import json


class SignUpRequest(Schema):
    name = fields.Str(default = "name")
    username = fields.Str(default = "username")
    password = fields.Str(default = "password")
    level = fields.Int(default = "level")

class AddItemRequest(Schema):
    item_id = fields.Str(default = "item_id")
    item_name = fields.Str(default = "item_name")
    calories_per_gm = fields.Str(default = "calories_per_gm")
    available_quantity = fields.Int(default = "available_quantity")
    restaurant_name = fields.Str(default = "restaurant_name")
    unit_price = fields.Float(default = "unit_price")


class CreateItemOrderRequest(Schema):
    item_id = fields.Str(default = "item_id")
    quantity = fields.Int(default = 0)

class PlaceOrderRequest(Schema):
    order_id = fields.Str(default = "order_id")   

class APIResponse(Schema):
    message = fields.Str(default="Success")

class LoginRequest(Schema):
    username = fields.Str(default="username")
    password = fields.Str(default="password")

class AddVendorRequest(Schema):
    user_id = fields.Str(default="user_id")

class CustomerOrdersRequest(Schema):
    customer_id = fields.Str(default = "customer_id")   

class GetVendorsResponse(Schema):
    vendors = fields.List(fields.Dict())

class ListItemsResponse(Schema):
    items = fields.List(fields.Dict())

class ListAllOrderResponse(Schema):
    allorders=fields.List(fields.Dict())

class CustomerOrdersResponse(Schema):
    custorders=fields.List(fields.Dict())

#  Restful way of creating APIs through Flask Restful
class SignUpAPI(MethodResource, Resource):    
    @doc(description='Sign Up API', tags=['SignUp API'])
    @use_kwargs(SignUpRequest, location=('json'))
    @marshal_with(APIResponse)  # marshalling    
    def post(self, **kwargs):        
        try:            
            user = User(
                uuid.uuid4(),
                kwargs['name'], 
                kwargs['username'], 
                kwargs['password'], 
                kwargs['level']
               )
            session['user_id']=None
            session['level']=None
            db.session.add(user)
            db.session.commit()
            return APIResponse().dump(dict(message='User is successfully registerd')), 200
        except Exception as e:
            print(str(e))
            return APIResponse().dump(dict(message=f'Not able to register user : {str(e)}')), 400
        

api.add_resource(SignUpAPI, '/signup')
docs.register(SignUpAPI)

class LoginAPI(MethodResource, Resource):
    @doc(description='Login API', tags=['Login API'])
    @use_kwargs(LoginRequest, location=('json'))
    @marshal_with(APIResponse)  # marshalling
    def post(self, **kwargs):
        try:
            user = User.query.filter_by(username=kwargs['username'], password = kwargs['password']).first()
            if user:
                print('logged in')
                session['user_id'] = user.user_id
                session['level'] = user.level
                print(f'User id : {str(session["user_id"])}')
                return APIResponse().dump(dict(message='User is successfully logged in')), 200
            else:
                return APIResponse().dump(dict(message='User not found')), 404
        except Exception as e:
            print(str(e))
            return APIResponse().dump(dict(message=f'Not able to login user : {str(e)}')), 400    
            
api.add_resource(LoginAPI, '/login')
docs.register(LoginAPI)

class LogoutAPI(MethodResource, Resource):
    @doc(description='Logout API', tags=['Logout API'])
    @marshal_with(APIResponse)  # marshalling
    def post(self):
        try:
            if session['user_id']:
                session['user_id'] = None
                session['level'] = None
                print('logged out')
                return APIResponse().dump(dict(message='User is successfully logged out')), 200
            else:
                print('user not found')
                return APIResponse().dump(dict(message='User is not logged in')), 401
        except Exception as e:
            print(str(e))
            return APIResponse().dump(dict(message=f'Not able to logout user : {str(e)}')), 400
            

api.add_resource(LogoutAPI, '/logout')
docs.register(LogoutAPI)


class AddVendorAPI(MethodResource, Resource):
    @doc(description='Add Vendor API', tags=['Add Vendor API'])
    @use_kwargs(AddVendorRequest, location=('json'))
    @marshal_with(APIResponse)
    def post(self, **kwargs):
        try:
            if session['level']==2: #Checking whether the user is admin 
                user = User.query.filter_by(user_id=kwargs['user_id'], level=0).first()
                if user:                
                    user.level  = 1
                    user.updated_ts = datetime.now()
                    db.session.commit()
                    print("Changed to vendor")
                    return APIResponse().dump(dict(message="Added as a vendor")), 200
                else:
                    print("User is not a customer")
                    return APIResponse().dump(dict(message="User is not a customer")), 404
            else:
                return APIResponse().dump(dict(message="Only admins are authorized to add vendors")), 404
        except Exception as e:
            return APIResponse().dump(dict(message=f'Not able to logout user : {str(e)}')), 400
                            

api.add_resource(AddVendorAPI, '/add_vendor')
docs.register(AddVendorAPI)


class GetVendorsAPI(MethodResource, Resource):
    @doc(description="Get Vendors API", tags=['Get vendor API'])
    @marshal_with(GetVendorsResponse)
    def get(self):
        try:
            if session['user_id']:                           
                vendors_items = db.session.query(User, Item).filter(User.user_id == Item.vendor_id).order_by(Item.vendor_id) 
                if vendors_items:
                    vendor_list=[]
                    for u, v in vendors_items:
                        vendor_dict={}
                        vendor_dict['vendor_id']=v.vendor_id
                        vendor_dict['name'] = u.name
                        vendor_dict['username'] = u.username                       
                        vendor_dict['restaurant_name'] = v.restaurant_name
                        vendor_dict['item_name'] = v.item_name
                        vendor_dict['unit_price'] = v.unit_price
                        # vendor_dict['calories_per_gm'] = v.calories_per_gm
                        vendor_list.append(vendor_dict)
                    print(vendor_list)
                    return GetVendorsResponse().dump(dict(vendors=vendor_list)), 200
                else:
                    return APIResponse().dump(dict(message='No vendors')), 404
            else:
                    return APIResponse().dump(dict(message='User not logged in')), 401
        except Exception as e:
            return APIResponse().dump(dict(message=f'Not able to list vendors : {str(e)}')), 400
            

api.add_resource(GetVendorsAPI, '/list_vendors')
docs.register(GetVendorsAPI)

class AddItemAPI(MethodResource, Resource):
    @doc(description='Add Item API', tags=['Add Item API'])
    @use_kwargs(AddItemRequest, location=('json'))
    @marshal_with(APIResponse)  # marshalling    
    def post(self, **kwargs):        
        try:     
            if session['user_id'] and session['level']==1:       
                item = Item(
                    kwargs['item_id'] ,  ###  uuid.uuid4()
                    session['user_id'], 
                    kwargs['item_name'], 
                    kwargs['calories_per_gm'], 
                    kwargs['available_quantity'],
                    kwargs['restaurant_name'],
                    kwargs['unit_price'])            
                            
                db.session.add(item)
                db.session.commit()
                return APIResponse().dump(dict(message='Item is successfully added')), 200
            else:
                return APIResponse().dump(dict(message='Only vendor can add items')), 404
        except Exception as e:
            print(str(e))
            return APIResponse().dump(dict(message=f'Not able to add item : {str(e)}')), 400
        
            
api.add_resource(AddItemAPI, '/add_item')
docs.register(AddItemAPI)


class ListItemsAPI(MethodResource, Resource):
    @doc(description="List Items API", tags=['List Items API'])
    @marshal_with(ListItemsResponse)
    def get(self):
        try:
            if session['user_id'] is not None:
                items = Item.query.all() # filter_by(vendor_id=session['user_id'])
                if items:
                    items_list=[]
                    for item in items:
                        items_dict={}
                        items_dict['vendor_id'] = item.vendor_id
                        items_dict['item_id'] = item.item_id
                        items_dict['item_name'] = item.item_name
                        items_dict['restaurant_name'] = item.restaurant_name
                        items_dict['available_quantity'] = item.available_quantity
                        items_dict['calories_per_gm'] = item.calories_per_gm
                        items_dict['unit_price'] = item.unit_price
                        items_list.append(items_dict)
                    print(items_list)
                    return ListItemsResponse().dump(dict(items=items_list)), 200
                else:
                    return APIResponse().dump(dict(message='No Items')), 404
            else:
                    return APIResponse().dump(dict(message='User not logged in')), 401
        except Exception as e:
            return APIResponse().dump(dict(message=f'Not able to list items : {str(e)}')), 400
            

api.add_resource(ListItemsAPI, '/list_items')
docs.register(ListItemsAPI)


class CreateItemOrderAPI(MethodResource, Resource):
    @doc(description ='Create Order Items API', tags=['Create Order Items API'])
    @use_kwargs(CreateItemOrderRequest, location=('json'))
    @marshal_with(APIResponse)
    
    def post(self, **kwargs):
        try:
            if session['user_id'] and session['level']==0:                
                qty = kwargs['quantity']
                if qty <= 0:
                    return APIResponse().dump(dict(message = 'Quantity must be more than 0.')), 404
                
                item = Item.query.filter_by(item_id=kwargs['item_id']).first()
                if item.available_quantity < qty:
                    return APIResponse().dump(dict(message = 'Required quantity not available')), 404
                
                item.available_quantity -= qty 

                ta = qty * item.unit_price
                order_id = uuid.uuid4()
                order = Order(
                    order_id,
                    session['user_id'],
                    ta
                )
                db.session.add(order)

                order_items = OrderItems(
                    uuid.uuid4(), 
                    order_id, 
                    kwargs['item_id'], 
                    kwargs['quantity']
                )
                db.session.add(order_items)            
                db.session.commit()
                return APIResponse().dump(dict(message='Successfully Added your items')), 200
            else:
                return APIResponse().dump(dict(message='Only Customer can place an order')), 401
        except Exception as e:
            return APIResponse().dump(dict(message=f'Not able to create an order: {str(e)}')), 400  


api.add_resource(CreateItemOrderAPI, '/create_items_order')
docs.register(CreateItemOrderAPI)


class PlaceOrderAPI(MethodResource, Resource):
    @doc(description ='Place Order API', tags=['Place Order API'])
    @use_kwargs(PlaceOrderRequest, location=('json'))
    @marshal_with(APIResponse)
    
    def post(self, **kwargs):
        try:
            if session['user_id'] and session['level']==0:                
                order = Order.query.filter_by(order_id = kwargs['order_id']).first()
                if order:
                    order.is_placed = 1
                    order.updated_ts = datetime.now()
                    db.session.commit()
                    return APIResponse().dump(dict(message='Successfully placed your order')), 200
                else:
                    return APIResponse().dump(dict(message=f'Please check the order_id')), 404               
            else:
                return APIResponse().dump(dict(message='Only Customer can place an order')), 404
        except Exception as e:
            return APIResponse().dump(dict(message=f'Not able to place order: {str(e)}')), 400   
            

api.add_resource(PlaceOrderAPI, '/place_order')
docs.register(PlaceOrderAPI)

class ListOrdersByCustomerAPI(MethodResource, Resource):
    @doc(description ="Customer Orders API", tags=['Customer orders API'])
    @use_kwargs(CustomerOrdersRequest, location=('json'))
    @marshal_with(CustomerOrdersResponse)

    def post(self, **kwargs):
        try:
            if session['user_id']:
                # custorders = Order.query.filter_by(user_id=session['user_id'])
                custorders = db.session.query(Order, OrderItems).filter(Order.order_id == OrderItems.order_id, Order.user_id==kwargs['customer_id']).order_by(Order.order_id) 
                if custorders:
                    orders_list=[]
                    for ord, orditems in custorders:
                        order_dict={}                        
                        order_dict['order_id']=ord.order_id
                        order_dict['item_id'] = orditems.item_id
                        order_dict['quantity'] = orditems.quantity
                        order_dict['total_amount'] = ord.total_amount
                        order_dict['is_placed'] = "Yes" if ord.is_placed else "No"
                        order_dict['created_ts'] = ord.created_ts
                        orders_list.append(order_dict)
                    
                    return CustomerOrdersResponse().dump(dict(custorders=orders_list)), 200
            else:
                return APIResponse().dump(dict(message="User not logged in.")), 401                
        except Exception as e:
            return APIResponse().dump(dict(message=f'Not able to list Orders : {str(e)}')), 400           
            

api.add_resource(ListOrdersByCustomerAPI, '/list_orders')
docs.register(ListOrdersByCustomerAPI)


class ListAllOrdersAPI(MethodResource, Resource):
    @doc(description ="List All Orders API", tags=['List all orders API'])
    @marshal_with(ListAllOrderResponse)

    def get(self):
        try:
            if session['user_id'] and session['level']==2:
                orders = Order.query.all()
                if orders:
                    orders_list=[]
                    for order in orders:
                        order_dict={}
                        order_dict['user_id'] = order.user_id
                        order_dict['total_amount'] = order.total_amount
                        order_dict['is_placed'] = order.is_placed
                        order_dict['created_ts'] = order.created_ts
                        orders_list.append(order_dict)                   
                    return ListAllOrderResponse().dump(dict(allorders=orders_list)), 200
            else:
                return APIResponse().dump(dict(message="Only Admins can view orders")), 404              
        except Exception as e:
            return APIResponse().dump(dict(message=f'Not able to list Orders : {str(e)}')), 400
            
api.add_resource(ListAllOrdersAPI, '/list_all_orders')
docs.register(ListAllOrdersAPI)