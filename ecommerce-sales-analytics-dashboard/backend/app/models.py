from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    signup_date = Column(Date, nullable=False)
    country = Column(String, nullable=False)
    segment = Column(String, nullable=False)  # Consumer, Corporate, Home Office

    orders = relationship("Order", back_populates="customer")

class Product(Base):
    __tablename__ = "products"

    product_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)      # e.g. Technology, Furniture, Office Supplies
    sub_category = Column(String, nullable=False)  # e.g. Phones, Chairs, Paper
    price = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)

    order_items = relationship("OrderItem", back_populates="product")

class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"), nullable=False)
    order_date = Column(Date, nullable=False)
    ship_date = Column(Date, nullable=True)
    ship_mode = Column(String, nullable=True)     # Standard Class, Second Class, First Class, Same Day
    status = Column(String, nullable=False)        # Delivered, Shipped, Processing, Cancelled

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    item_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, ForeignKey("orders.order_id"), nullable=False)
    product_id = Column(String, ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    sales = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    profit = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

class WebTraffic(Base):
    __tablename__ = "web_traffic"

    session_id = Column(String, primary_key=True, index=True)
    traffic_date = Column(Date, nullable=False)
    visitor_id = Column(String, nullable=False)
    page_views = Column(Integer, default=1)
    added_to_cart = Column(Boolean, default=False)
    purchased = Column(Boolean, default=False)
