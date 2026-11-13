from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, text
import pandas as pd
import numpy as np
import time
from .models import Customer, Product, Order, OrderItem, WebTraffic

def get_kpis(db: Session, start_date: date = None, end_date: date = None, segment: str = None, category: str = None):
    # Base query for order items
    query = db.query(
        OrderItem.sales,
        OrderItem.profit,
        Order.order_id,
        Order.customer_id
    ).join(Order).join(Product)
    
    if start_date:
        query = query.filter(Order.order_date >= start_date)
    if end_date:
        query = query.filter(Order.order_date <= end_date)
    if segment:
        query = query.join(Customer).filter(Customer.segment == segment)
    if category:
        query = query.filter(Product.category == category)
        
    items = query.all()
    
    total_revenue = sum(item.sales for item in items)
    total_profit = sum(item.profit for item in items)
    unique_orders = len(set(item.order_id for item in items))
    unique_customers = len(set(item.customer_id for item in items))
    
    profit_margin = (total_profit / total_revenue) if total_revenue > 0 else 0.0
    aov = (total_revenue / unique_orders) if unique_orders > 0 else 0.0
    
    # Traffic query for conversion rate
    traffic_query = db.query(WebTraffic)
    if start_date:
        traffic_query = traffic_query.filter(WebTraffic.traffic_date >= start_date)
    if end_date:
        traffic_query = traffic_query.filter(WebTraffic.traffic_date <= end_date)
        
    total_sessions = traffic_query.count()
    total_purchases = traffic_query.filter(WebTraffic.purchased == True).count()
    
    conversion_rate = (total_purchases / total_sessions) if total_sessions > 0 else 0.0
    
    # Repeat Customer Rate (customers with >= 2 orders in entire history, or filtered history)
    cust_orders_query = db.query(Order.customer_id, func.count(Order.order_id)).group_by(Order.customer_id)
    if start_date:
        cust_orders_query = cust_orders_query.filter(Order.order_date >= start_date)
    if end_date:
        cust_orders_query = cust_orders_query.filter(Order.order_date <= end_date)
        
    cust_orders = cust_orders_query.all()
    total_buying_customers = len(cust_orders)
    repeat_customers = sum(1 for c in cust_orders if c[1] >= 2)
    
    repeat_customer_rate = (repeat_customers / total_buying_customers) if total_buying_customers > 0 else 0.0
    
    return {
        "total_revenue": round(total_revenue, 2),
        "total_profit": round(total_profit, 2),
        "profit_margin": round(profit_margin * 100, 2),  # Percentage
        "average_order_value": round(aov, 2),
        "conversion_rate": round(conversion_rate * 100, 2),  # Percentage
        "repeat_customer_rate": round(repeat_customer_rate * 100, 2),  # Percentage
        "total_orders": unique_orders,
        "total_customers": unique_customers
    }

def get_trends(db: Session, start_date: date = None, end_date: date = None, segment: str = None, category: str = None):
    # We will group by order_date
    query = db.query(
        Order.order_date,
        func.sum(OrderItem.sales).label("sales"),
        func.sum(OrderItem.profit).label("profit"),
        func.count(func.distinct(Order.order_id)).label("orders")
    ).join(OrderItem).join(Product)
    
    if start_date:
        query = query.filter(Order.order_date >= start_date)
    if end_date:
        query = query.filter(Order.order_date <= end_date)
    if segment:
        query = query.join(Customer).filter(Customer.segment == segment)
    if category:
        query = query.filter(Product.category == category)
        
    results = query.group_by(Order.order_date).order_by(Order.order_date).all()
    
    return [
        {
            "date": r.order_date.isoformat(),
            "sales": round(r.sales, 2),
            "profit": round(r.profit, 2),
            "orders": r.orders
        }
        for r in results
    ]

def get_categories(db: Session, start_date: date = None, end_date: date = None, segment: str = None):
    # Group by category & sub_category
    query = db.query(
        Product.category,
        Product.sub_category,
        func.sum(OrderItem.sales).label("sales"),
        func.sum(OrderItem.profit).label("profit"),
        func.sum(OrderItem.quantity).label("quantity")
    ).join(OrderItem).join(Order)
    
    if start_date:
        query = query.filter(Order.order_date >= start_date)
    if end_date:
        query = query.filter(Order.order_date <= end_date)
    if segment:
        query = query.join(Customer).filter(Customer.segment == segment)
        
    results = query.group_by(Product.category, Product.sub_category).all()
    
    data = []
    for r in results:
        margin = (r.profit / r.sales) if r.sales > 0 else 0.0
        data.append({
            "category": r.category,
            "sub_category": r.sub_category,
            "sales": round(r.sales, 2),
            "profit": round(r.profit, 2),
            "quantity": int(r.quantity),
            "profit_margin": round(margin * 100, 2)
        })
    return data

def get_top_products(db: Session, limit: int = 10, category: str = None):
    query = db.query(
        Product.product_id,
        Product.name,
        Product.category,
        func.sum(OrderItem.sales).label("sales"),
        func.sum(OrderItem.profit).label("profit"),
        func.sum(OrderItem.quantity).label("quantity")
    ).join(OrderItem).group_by(Product.product_id, Product.name, Product.category)
    
    if category:
        query = query.filter(Product.category == category)
        
    results = query.order_by(func.sum(OrderItem.sales).desc()).limit(limit).all()
    
    return [
        {
            "product_id": r.product_id,
            "name": r.name,
            "category": r.category,
            "sales": round(r.sales, 2),
            "profit": round(r.profit, 2),
            "quantity_sold": int(r.quantity)
        }
        for r in results
    ]

def get_funnel(db: Session, start_date: date = None, end_date: date = None):
    # Web Traffic Funnel
    query = db.query(WebTraffic)
    if start_date:
        query = query.filter(WebTraffic.traffic_date >= start_date)
    if end_date:
        query = query.filter(WebTraffic.traffic_date <= end_date)
        
    sessions = query.all()
    
    total_sessions = len(sessions)
    cart_sessions = sum(1 for s in sessions if s.added_to_cart or s.purchased)
    purchased_sessions = sum(1 for s in sessions if s.purchased)
    
    return [
        {"stage": "1. Sessions", "count": total_sessions, "percentage": 100.0},
        {"stage": "2. Add to Cart", "count": cart_sessions, "percentage": round((cart_sessions / total_sessions) * 100, 2) if total_sessions > 0 else 0.0},
        {"stage": "3. Purchase", "count": purchased_sessions, "percentage": round((purchased_sessions / total_sessions) * 100, 2) if total_sessions > 0 else 0.0}
    ]

def get_cohorts(db: Session):
    """
    Generate Monthly Cohort Retention Heatmap using Pandas
    """
    # 1. Read customers & orders from SQLite
    orders_df = pd.read_sql_query(
        "SELECT order_id, customer_id, order_date FROM orders WHERE status != 'Cancelled'", 
        db.bind
    )
    
    if orders_df.empty:
        return []
        
    # Convert date column to datetime
    orders_df['order_date'] = pd.to_datetime(orders_df['order_date'])
    
    # 2. Assign Cohort Month (Month of Customer's First Purchase)
    orders_df['order_month'] = orders_df['order_date'].dt.to_period('M')
    orders_df['cohort'] = orders_df.groupby('customer_id')['order_date'].transform('min').dt.to_period('M')
    
    # 3. Group by cohort and order_month
    cohort_group = orders_df.groupby(['cohort', 'order_month']).agg(n_customers=('customer_id', 'nunique')).reset_index()
    
    # 4. Calculate period index (number of months since cohort start)
    # The result of subtraction of periods is an integer offset
    cohort_group['period'] = (cohort_group['order_month'] - cohort_group['cohort']).apply(lambda x: x.n)
    
    # Pivot cohort table
    cohort_pivot = cohort_group.pivot(index='cohort', columns='period', values='n_customers')
    
    # Extract size of each cohort (month 0 size)
    cohort_sizes = cohort_pivot.iloc[:, 0]
    
    # Divide row-wise by size to get retention percentage
    retention = cohort_pivot.divide(cohort_sizes, axis=0)
    
    # Fill NaN values and convert to percentage
    retention = retention.fillna(0) * 100
    
    # Format return list
    cohort_list = []
    for idx, row in retention.iterrows():
        cohort_str = str(idx) # e.g. '2025-07'
        size = int(cohort_sizes.loc[idx])
        periods_data = {}
        for period_col in retention.columns:
            periods_data[str(period_col)] = round(float(row[period_col]), 2)
            
        cohort_list.append({
            "cohort": cohort_str,
            "size": size,
            "retention": periods_data
        })
        
    return cohort_list

def execute_safe_sql(db: Session, query: str):
    """
    Executes a SELECT query against the SQLite database and returns headers and rows.
    Implements security guards.
    """
    query_stripped = query.strip().upper()
    
    # Security checks: only allow SELECT queries and block modifications
    if not query_stripped.startswith("SELECT"):
        return {
            "columns": [],
            "rows": [],
            "execution_time_ms": 0.0,
            "error": "Security Restriction: Only read-only SELECT queries are allowed."
        }
        
    blacklisted_keywords = ["DELETE", "DROP", "INSERT", "UPDATE", "CREATE", "ALTER", "REPLACE", "TRUNCATE", "RENAME"]
    for word in blacklisted_keywords:
        # Check if keyword is a full word in the query
        if f" {word} " in f" {query_stripped} " or query_stripped.startswith(word):
            return {
                "columns": [],
                "rows": [],
                "execution_time_ms": 0.0,
                "error": f"Security Restriction: Write operations ('{word}') are prohibited."
            }
            
    start_time = time.time()
    try:
        # Execute query
        result = db.execute(text(query))
        
        # Get columns
        columns = list(result.keys())
        
        # Get rows (convert values to string or JSON-compatible types)
        rows = []
        for row in result.fetchall():
            row_vals = []
            for val in row:
                if isinstance(val, (datetime, date)):
                    row_vals.append(val.isoformat())
                else:
                    row_vals.append(val)
            rows.append(row_vals)
            
        execution_time = (time.time() - start_time) * 1000
        
        return {
            "columns": columns,
            "rows": rows[:100],  # Cap at 100 rows for display
            "execution_time_ms": round(execution_time, 2),
            "error": None
        }
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        return {
            "columns": [],
            "rows": [],
            "execution_time_ms": round(execution_time, 2),
            "error": str(e)
        }

def get_recommendations(db: Session):
    """
    Generate business and data-driven recommendations based on current database state.
    """
    recommendations = []
    
    # Recommendation 1: Negative profit products/categories
    neg_profit_query = db.query(
        Product.category, Product.sub_category, Product.name, func.sum(OrderItem.profit).label("total_profit")
    ).join(OrderItem, Product.product_id == OrderItem.product_id).group_by(Product.product_id, Product.category, Product.sub_category, Product.name).all()
    
    neg_items = [item for item in neg_profit_query if item.total_profit < 0]
    if neg_items:
        worst_item = min(neg_items, key=lambda x: x.total_profit)
        recommendations.append({
            "id": 1,
            "category": "Pricing & Margin",
            "title": f"Review Pricing for {worst_item.name}",
            "description": f"The product '{worst_item.name}' in sub-category '{worst_item.sub_category}' has generated a net loss of ${abs(round(worst_item.total_profit, 2))} due to steep discounting. Recommend capping promotional discounts to 15%.",
            "impact": "High",
            "estimated_val": round(abs(worst_item.total_profit), 2)
        })
    else:
        recommendations.append({
            "id": 1,
            "category": "Pricing & Margin",
            "title": "Promotional Discount Optimization",
            "description": "All categories show positive profitability. Recommend testing a dynamic pricing model on high-margin Technology categories to maximize revenue during peak seasonal hours.",
            "impact": "Medium",
            "estimated_val": 1500.00
        })

    # Recommendation 2: Cart Abandonment from Web Traffic
    sessions = db.query(WebTraffic).all()
    total_sessions = len(sessions)
    cart_sessions = sum(1 for s in sessions if s.added_to_cart or s.purchased)
    purchased_sessions = sum(1 for s in sessions if s.purchased)
    
    abandonment_rate = ((cart_sessions - purchased_sessions) / cart_sessions) if cart_sessions > 0 else 0.0
    if abandonment_rate > 0.65:
        # High abandonment
        potential_revenue_lost = (cart_sessions - purchased_sessions) * 120.00 * 0.10 # Assume 10% recovery of $120 AOV
        recommendations.append({
            "id": 2,
            "category": "Checkout Optimization",
            "title": "Reduce Cart Abandonment Rate",
            "description": f"Currently, {round(abandonment_rate * 100, 1)}% of users who add products to their cart do not complete the purchase. Implement cart abandonment recovery emails and guest checkout options.",
            "impact": "High",
            "estimated_val": round(potential_revenue_lost, 2)
        })
    else:
        recommendations.append({
            "id": 2,
            "category": "Marketing & Funnel",
            "title": "Traffic Acquisition Campaign",
            "description": "Conversion funnel is performing efficiently. Focus budget on top-of-funnel (TOF) Google Shopping Ads for top-selling Technology products to drive new traffic.",
            "impact": "Medium",
            "estimated_val": 2400.00
        })

    # Recommendation 3: Customer Segment Analysis
    segment_revenue = db.query(
        Customer.segment, func.sum(OrderItem.sales).label("sales")
    ).join(Order, Customer.customer_id == Order.customer_id).join(OrderItem, Order.order_id == OrderItem.order_id).group_by(Customer.segment).all()
    
    total_rev = sum(s.sales for s in segment_revenue)
    home_office_rev = next((s.sales for s in segment_revenue if s.segment == "Home Office"), 0.0)
    home_office_share = (home_office_rev / total_rev) if total_rev > 0 else 0.0
    
    if home_office_share < 0.20:
        recommendations.append({
            "id": 3,
            "category": "Customer Segmentation",
            "title": "Target Home Office Segment Expansion",
            "description": f"The Home Office customer segment currently accounts for only {round(home_office_share * 100, 1)}% of revenue. Recommend launching targeted B2C email newsletters featuring desk chairs and monitor bundles.",
            "impact": "Medium",
            "estimated_val": 1250.00
        })
    else:
        recommendations.append({
            "id": 3,
            "category": "Loyalty Program",
            "title": "VIP Corporate Loyalty Program",
            "description": "Corporate segment contributes over 30% of revenue with a high Average Order Value. Establish a Corporate VIP Loyalty Tier to incentivize repeat annual purchases.",
            "impact": "High",
            "estimated_val": 3500.00
        })

    return recommendations
