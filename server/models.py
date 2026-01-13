from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import validates
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime

metadata = MetaData(naming_convention={
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
})

db = SQLAlchemy(metadata=metadata)


class Customer(db.Model, SerializerMixin):
    __tablename__ = 'customers'
    
    
    serialize_rules = ('-orders.customer',)
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    
    orders = db.relationship('Order', back_populates='customer', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Customer {self.id}: {self.username}>'


class Staff(db.Model, SerializerMixin):
    __tablename__ = 'staff'
    
    
    serialize_rules = ('-orders.staff',)
    
    id = db.Column(db.Integer, primary_key=True)
    staff_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    
    orders = db.relationship('Order', back_populates='staff', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Staff {self.id}: {self.staff_name} - {self.role}>'


class Table(db.Model, SerializerMixin):
    __tablename__ = 'tables'
    
    
    serialize_rules = ('-orders.table',)
    
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), default='available')  # available, occupied, reserved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
   
    orders = db.relationship('Order', back_populates='table', cascade='all, delete-orphan')
    
    @validates('status')
    def validate_status(self, key, status):
        valid_statuses = ['available', 'occupied', 'reserved']
        if status not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return status
    
    def __repr__(self):
        return f'<Table {self.id}: {self.status}>'


class Menu(db.Model, SerializerMixin):
    __tablename__ = 'menu'
    
   
    serialize_rules = ('-order_items.meal',)
    
    id = db.Column(db.Integer, primary_key=True)
    meal_name = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(255))
    price = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)
    
    
    order_items = db.relationship('OrderItem', back_populates='meal', cascade='all, delete-orphan')
    
    @validates('price')
    def validate_price(self, key, price):
        if price < 0:
            raise ValueError("Price must be positive")
        return price
    
    def __repr__(self):
        return f'<Menu {self.id}: {self.meal_name} - ${self.price}>'


class Order(db.Model, SerializerMixin):
    __tablename__ = 'orders'
    
    
    serialize_rules = ('-customer.orders', '-staff.orders', '-table.orders', 
                      '-order_items.order', '-payments.order')
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, preparing, served, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    
    customer = db.relationship('Customer', back_populates='orders')
    staff = db.relationship('Staff', back_populates='orders')
    table = db.relationship('Table', back_populates='orders')
    order_items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    payments = db.relationship('Payment', back_populates='order', cascade='all, delete-orphan')
    
    @validates('status')
    def validate_status(self, key, status):
        valid_statuses = ['pending', 'preparing', 'served', 'completed', 'cancelled']
        if status not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return status
    
    def __repr__(self):
        return f'<Order {self.id}: Table {self.table_id} - {self.status}>'


class OrderItem(db.Model, SerializerMixin):
    __tablename__ = 'order_items'
    
   
    serialize_rules = ('-order.order_items', '-meal.order_items')
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    meal_id = db.Column(db.Integer, db.ForeignKey('menu.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    
   
    order = db.relationship('Order', back_populates='order_items')
    meal = db.relationship('Menu', back_populates='order_items')
    
    @validates('quantity')
    def validate_quantity(self, key, quantity):
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")
        return quantity
    
    def __repr__(self):
        return f'<OrderItem {self.id}: Order {self.order_id} - Meal {self.meal_id} x{self.quantity}>'


class Payment(db.Model, SerializerMixin):
    __tablename__ = 'payments'
    
    
    serialize_rules = ('-order.payments', '-finances.payment')
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # cash, card, mobile_money
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, refunded
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
   
    order = db.relationship('Order', back_populates='payments')
    finances = db.relationship('Finance', back_populates='payment', cascade='all, delete-orphan')
    
    @validates('total_amount')
    def validate_total_amount(self, key, total_amount):
        if total_amount < 0:
            raise ValueError("Total amount must be positive")
        return total_amount
    
    @validates('payment_method')
    def validate_payment_method(self, key, payment_method):
        valid_methods = ['cash', 'card', 'mobile_money', 'credit']
        if payment_method not in valid_methods:
            raise ValueError(f"Payment method must be one of: {', '.join(valid_methods)}")
        return payment_method
    
    @validates('status')
    def validate_status(self, key, status):
        valid_statuses = ['pending', 'completed', 'failed', 'refunded']
        if status not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return status
    
    def __repr__(self):
        return f'<Payment {self.id}: Order {self.order_id} - ${self.total_amount} - {self.status}>'


class Finance(db.Model, SerializerMixin):
    __tablename__ = 'finances'
    
    
    serialize_rules = ('-payment.finances',)
    
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False)
    total_income = db.Column(db.Numeric(10, 2), nullable=False)
    
    
    payment = db.relationship('Payment', back_populates='finances')
    
    @validates('total_income')
    def validate_total_income(self, key, total_income):
        if total_income < 0:
            raise ValueError("Total income must be positive")
        return total_income
    
    def __repr__(self):
        return f'<Finance {self.id}: Payment {self.payment_id} - Income ${self.total_income}>'