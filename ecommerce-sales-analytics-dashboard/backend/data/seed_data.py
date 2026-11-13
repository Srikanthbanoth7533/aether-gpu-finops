import os
import sys
import random
from datetime import datetime, timedelta, date

# Add the parent directory of backend/data to sys.path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import engine, Base, SessionLocal
from app.models import Customer, Product, Order, OrderItem, WebTraffic

# Product Catalog Templates (Category, Sub-Category, Name, Price, Cost)
PRODUCT_TEMPLATES = [
    # Technology
    ("Technology", "Phones", "Apple iPhone 15 Pro", 999.0, 600.0),
    ("Technology", "Phones", "Samsung Galaxy S24 Ultra", 1199.0, 750.0),
    ("Technology", "Laptops", "Dell XPS 15 Laptop", 1899.0, 1300.0),
    ("Technology", "Laptops", "MacBook Air M3", 1099.0, 700.0),
    ("Technology", "Accessories", "Logitech MX Master 3S Mouse", 99.0, 45.0),
    ("Technology", "Accessories", "Keychron K2 Mechanical Keyboard", 89.0, 40.0),
    ("Technology", "Accessories", "Anker USB-C Hub 8-in-1", 49.0, 20.0),
    ("Technology", "Monitors", "Samsung 34\" Odyssey OLED Monitor", 899.0, 550.0),
    ("Technology", "Monitors", "Dell 27\" 4K USB-C Monitor", 349.0, 220.0),
    ("Technology", "Audio", "Sony WH-1000XM5 Headphones", 398.0, 240.0),

    # Furniture
    ("Furniture", "Chairs", "Herman Miller Aeron Chair", 1499.0, 950.0),
    ("Furniture", "Chairs", "Steelcase Gesture Chair", 1299.0, 800.0),
    ("Furniture", "Chairs", "Ergonomic Mesh Task Chair", 249.0, 150.0),
    ("Furniture", "Desks", "IKEA Bekant Motorized Sit/Stand Desk", 649.0, 450.0),
    ("Furniture", "Desks", "L-Shaped Corner Executive Desk", 499.0, 350.0),
    ("Furniture", "Desks", "Simple Compact Computer Desk", 119.0, 70.0),
    ("Furniture", "Bookcases", "5-Tier Wooden Bookcase", 189.0, 130.0),
    ("Furniture", "Bookcases", "Industrial Metal Floating Shelves", 79.0, 45.0),
    ("Furniture", "Tables", "Solid Oak Dining Table", 799.0, 550.0),
    ("Furniture", "Tables", "Modern Glass Coffee Table", 199.0, 140.0),

    # Office Supplies
    ("Office Supplies", "Paper", "Premium Letter Printer Paper (Case)", 45.0, 15.0),
    ("Office Supplies", "Paper", "Ruled Legal Pads (12-pack)", 18.0, 6.0),
    ("Office Supplies", "Art & Writing", "Pilot G2 Gel Pens (24-pack)", 22.0, 8.0),
    ("Office Supplies", "Art & Writing", "Sharpie Permanent Markers (12-pack)", 12.0, 4.0),
    ("Office Supplies", "Binders", "Heavy Duty D-Ring 3-Inch Binder", 9.0, 3.0),
    ("Office Supplies", "Binders", "Plastic Sheet Protectors (100-pack)", 8.0, 2.5),
    ("Office Supplies", "Organization", "Mesh Desk Organizer Caddy", 15.0, 5.0),
    ("Office Supplies", "Organization", "Plastic Storage Bins (6-pack)", 35.0, 12.0),
    ("Office Supplies", "Envelopes & Shipping", "Self-Seal Bubble Mailers (50-pack)", 24.0, 8.0),
    ("Office Supplies", "Envelopes & Shipping", "Heavy Duty Packing Tape (6-pack)", 18.0, 6.0),
]

CITIES_COUNTRIES = [
    ("United States", "New York"),
    ("United States", "Los Angeles"),
    ("United States", "Chicago"),
    ("United States", "San Francisco"),
    ("United States", "Austin"),
    ("Canada", "Toronto"),
    ("Canada", "Vancouver"),
    ("United Kingdom", "London"),
    ("Germany", "Berlin"),
    ("France", "Paris"),
    ("Australia", "Sydney"),
    ("Japan", "Tokyo"),
]

FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth",
               "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

def seed_database():
    print("Initializing database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        print("Generating customers...")
        customers = []
        customer_ids = []
        segments = ["Consumer", "Corporate", "Home Office"]
        segment_weights = [0.55, 0.30, 0.15]
        
        start_date = datetime.now() - timedelta(days=365)
        
        for i in range(1, 201):
            cust_id = f"CUST-{i:04d}"
            name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            email = f"{name.lower().replace(' ', '.')}.{i:04d}@example.com"
            # signup date in the past year
            signup_dt = start_date + timedelta(days=random.randint(0, 180))
            country, city = random.choice(CITIES_COUNTRIES)
            segment = random.choices(segments, weights=segment_weights)[0]
            
            customer = Customer(
                customer_id=cust_id,
                name=name,
                email=email,
                signup_date=signup_dt.date(),
                country=country,
                segment=segment
            )
            customers.append(customer)
            customer_ids.append(cust_id)
            db.add(customer)
            
        print("Generating products...")
        products = []
        for i, (cat, subcat, name, price, cost) in enumerate(PRODUCT_TEMPLATES, 1):
            prod_id = f"PROD-{i:03d}"
            product = Product(
                product_id=prod_id,
                name=name,
                category=cat,
                sub_category=subcat,
                price=price,
                cost=cost
            )
            products.append(product)
            db.add(product)
            
        db.commit()
        
        print("Generating orders, items, and web traffic...")
        orders = []
        order_items = []
        web_traffic = []
        
        # We will loop day by day over the past 365 days
        current_date = start_date
        end_date = datetime.now()
        
        order_count = 1
        session_count = 1
        
        # Keep track of visitor IDs
        visitor_ids = [f"VIS-{random.randint(10000, 99999)}" for _ in range(500)]
        
        # Map customer_id to a specific visitor_id so return customers have the same visitor_id
        cust_visitor_map = {}
        for c_id in customer_ids:
            cust_visitor_map[c_id] = random.choice(visitor_ids)
            
        while current_date <= end_date:
            curr_date_only = current_date.date()
            
            # 1. Determine number of traffic sessions on this day
            # Apply seasonality (higher traffic in Nov/Dec, lower in Jan)
            month = current_date.month
            seasonality_factor = 1.0
            if month in [11, 12]:  # Holiday season
                seasonality_factor = 1.6
            elif month in [1, 2]:  # Post-holiday slump
                seasonality_factor = 0.7
                
            # Day of week factor (more traffic on weekdays)
            weekday = current_date.weekday()
            weekday_factor = 1.2 if weekday < 5 else 0.8
            
            base_sessions = random.randint(10, 25)
            daily_sessions_count = int(base_sessions * seasonality_factor * weekday_factor)
            
            # We want to target an overall ~2.5% conversion rate.
            # So out of daily_sessions_count, some will purchase.
            purchasing_sessions_today = []
            non_purchasing_sessions_count = daily_sessions_count
            
            # Determine number of orders today (e.g. 0 to 4)
            base_orders = random.choices([0, 1, 2, 3, 4], weights=[0.25, 0.4, 0.2, 0.1, 0.05])[0]
            daily_orders_count = int(base_orders * seasonality_factor * weekday_factor)
            
            # Generate orders for today
            for _ in range(daily_orders_count):
                order_id = f"ORD-{order_count:05d}"
                cust_id = random.choice(customer_ids)
                
                # Check if customer has already signed up by this date
                cust_obj = next(c for c in customers if c.customer_id == cust_id)
                if cust_obj.signup_date > curr_date_only:
                    # Not signed up yet, let's shift signup date or choose another signed up customer
                    signed_up_customers = [c.customer_id for c in customers if c.signup_date <= curr_date_only]
                    if signed_up_customers:
                        cust_id = random.choice(signed_up_customers)
                    else:
                        continue # Skip generating order if no one signed up yet
                
                # Ship date: 1 to 7 days after order date
                ship_days = random.randint(1, 7)
                ship_date = curr_date_only + timedelta(days=ship_days)
                
                ship_mode = random.choices(
                    ["Standard Class", "Second Class", "First Class", "Same Day"],
                    weights=[0.6, 0.2, 0.15, 0.05]
                )[0]
                
                status = random.choices(
                    ["Delivered", "Shipped", "Processing", "Cancelled"],
                    weights=[0.85, 0.1, 0.03, 0.02]
                )[0]
                
                # Order instance
                new_order = Order(
                    order_id=order_id,
                    customer_id=cust_id,
                    order_date=curr_date_only,
                    ship_date=ship_date if status != "Cancelled" else None,
                    ship_mode=ship_mode if status != "Cancelled" else None,
                    status=status
                )
                
                # Select random products for this order
                num_items = random.randint(1, 4)
                order_products = random.sample(products, num_items)
                
                total_order_profit = 0
                total_order_sales = 0
                
                for prod in order_products:
                    quantity = random.randint(1, 3)
                    
                    # Discount strategy
                    # Certain products (especially underperforming furniture or office items) get higher discounts
                    # Some Furniture items get deep discounts (up to 50%) causing negative profit
                    discount = 0.0
                    if prod.category == "Furniture":
                        discount = random.choices([0.0, 0.1, 0.2, 0.4, 0.5], weights=[0.4, 0.3, 0.15, 0.1, 0.05])[0]
                    elif prod.category == "Office Supplies":
                        discount = random.choices([0.0, 0.05, 0.1, 0.2], weights=[0.6, 0.2, 0.15, 0.05])[0]
                    else:  # Technology
                        discount = random.choices([0.0, 0.05, 0.1], weights=[0.8, 0.15, 0.05])[0]
                    
                    sales_val = prod.price * quantity * (1.0 - discount)
                    cost_val = prod.cost * quantity
                    profit_val = sales_val - cost_val
                    
                    order_item = OrderItem(
                        order_id=order_id,
                        product_id=prod.product_id,
                        quantity=quantity,
                        sales=round(sales_val, 2),
                        discount=discount,
                        profit=round(profit_val, 2)
                    )
                    order_items.append(order_item)
                    db.add(order_item)
                
                db.add(new_order)
                orders.append(new_order)
                
                # Map this order to a purchasing traffic session
                visitor_id = cust_visitor_map[cust_id]
                session_id = f"SESS-{session_count:06d}"
                session_count += 1
                
                p_session = WebTraffic(
                    session_id=session_id,
                    traffic_date=curr_date_only,
                    visitor_id=visitor_id,
                    page_views=random.randint(5, 15),
                    added_to_cart=True,
                    purchased=True
                )
                web_traffic.append(p_session)
                db.add(p_session)
                
                order_count += 1
                
            # 2. Generate the rest of the daily traffic sessions (non-purchasing)
            for _ in range(non_purchasing_sessions_count):
                session_id = f"SESS-{session_count:06d}"
                session_count += 1
                
                # Sometime use an existing customer's visitor ID, sometimes a new random one
                if random.random() < 0.3:
                    visitor_id = random.choice(visitor_ids)
                else:
                    visitor_id = f"VIS-{random.randint(10000, 99999)}"
                    
                # Did they add to cart?
                added_to_cart = random.choices([True, False], weights=[0.12, 0.88])[0]
                
                # Page views are higher if they added to cart
                if added_to_cart:
                    page_views = random.randint(3, 8)
                else:
                    page_views = random.randint(1, 4)
                    
                np_session = WebTraffic(
                    session_id=session_id,
                    traffic_date=curr_date_only,
                    visitor_id=visitor_id,
                    page_views=page_views,
                    added_to_cart=added_to_cart,
                    purchased=False
                )
                web_traffic.append(np_session)
                db.add(np_session)
                
            current_date += timedelta(days=1)
            
        print("Saving to database...")
        db.commit()
        
        # Verify seeding counts
        print("\nDatabase Seeded Successfully!")
        print(f"Total Customers: {db.query(Customer).count()}")
        print(f"Total Products: {db.query(Product).count()}")
        print(f"Total Orders: {db.query(Order).count()}")
        print(f"Total Order Items: {db.query(OrderItem).count()}")
        print(f"Total Web Traffic Sessions: {db.query(WebTraffic).count()}")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
