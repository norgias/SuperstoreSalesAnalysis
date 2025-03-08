from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import sqlite3
import os
from datetime import datetime

# Create Flask application
app = Flask(__name__)

# Configure database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sales_data_proper.db'  
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Define a simple data model
class DataPoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    value = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'<DataPoint {self.category}: {self.value}>'

# Helper function to connect to the database directly (for raw SQL queries)
def get_db_connection():
    conn = sqlite3.connect('sales_data_proper.db')
    conn.row_factory = sqlite3.Row
    return conn

# Helper function to execute query and convert to JSON
def query_to_json(query, params=()):
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df.to_dict(orient='records')

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    data_points = DataPoint.query.all()
    result = []
    
    for point in data_points:
        result.append({
            'id': point.id,
            'category': point.category,
            'value': point.value,
            'date': point.date.isoformat()
        })
    
    return jsonify(result)

# New API Routes for Tableau Integration

# Route for total sales by region
@app.route('/api/sales_by_region', methods=['GET'])
def sales_by_region():
    query = """
    SELECT Region, SUM(Sales) as TotalSales, SUM(Profit) as TotalProfit
    FROM orders
    GROUP BY Region
    ORDER BY TotalSales DESC
    """
    return jsonify(query_to_json(query))

# Route for total sales by category
@app.route('/api/sales_by_category', methods=['GET'])
def sales_by_category():
    query = """
    SELECT Category, SUM(Sales) as TotalSales, SUM(Profit) as TotalProfit
    FROM orders
    GROUP BY Category
    ORDER BY TotalSales DESC
    """
    return jsonify(query_to_json(query))

# Route for total sales by subcategory
@app.route('/api/sales_by_subcategory', methods=['GET'])
def sales_by_subcategory():
    query = """
    SELECT Category, Sub_Category, SUM(Sales) as TotalSales, SUM(Profit) as TotalProfit
    FROM orders
    GROUP BY Category, Sub_Category
    ORDER BY Category, TotalSales DESC
    """
    return jsonify(query_to_json(query))

# Route for sales trends over time (monthly)
@app.route('/api/monthly_sales', methods=['GET'])
def monthly_sales():
    query = """
    SELECT 
        strftime('%Y-%m', Order_Date) as Month,
        SUM(Sales) as TotalSales,
        SUM(Profit) as TotalProfit
    FROM orders
    GROUP BY Month
    ORDER BY Month
    """
    return jsonify(query_to_json(query))

# Route for sales trends over time (quarterly)
@app.route('/api/quarterly_sales', methods=['GET'])
def quarterly_sales():
    query = """
    SELECT 
        strftime('%Y', Order_Date) || '-Q' || CAST((strftime('%m', Order_Date) + 2) / 3 AS TEXT) as Quarter,
        SUM(Sales) as TotalSales,
        SUM(Profit) as TotalProfit
    FROM orders
    GROUP BY Quarter
    ORDER BY Quarter
    """
    return jsonify(query_to_json(query))

# Route for sales trends over time (yearly)
@app.route('/api/yearly_sales', methods=['GET'])
def yearly_sales():
    query = """
    SELECT 
        strftime('%Y', Order_Date) as Year,
        SUM(Sales) as TotalSales,
        SUM(Profit) as TotalProfit
    FROM orders
    GROUP BY Year
    ORDER BY Year
    """
    return jsonify(query_to_json(query))

# Route for profit margins by product
@app.route('/api/product_profit_margins', methods=['GET'])
def product_profit_margins():
    query = """
    SELECT 
        Product_ID,
        Product_Name,
        SUM(Sales) as TotalSales,
        SUM(Profit) as TotalProfit,
        (SUM(Profit) / SUM(Sales) * 100) as ProfitMargin
    FROM orders
    GROUP BY Product_ID, Product_Name
    HAVING TotalSales > 0
    ORDER BY ProfitMargin DESC
    """
    return jsonify(query_to_json(query))

# Route for customer segmentation data
@app.route('/api/customer_segments', methods=['GET'])
def customer_segments():
    query = """
    SELECT 
        Customer_ID,
        Customer_Name,
        Segment,
        COUNT(DISTINCT Order_ID) as OrderCount,
        SUM(Sales) as TotalSpent,
        AVG(Sales) as AvgOrderValue
    FROM orders
    GROUP BY Customer_ID, Customer_Name, Segment
    ORDER BY TotalSpent DESC
    """
    return jsonify(query_to_json(query))

# Route for top performing products
@app.route('/api/top_products', methods=['GET'])
def top_products():
    query = """
    SELECT 
        Product_ID,
        Product_Name,
        Category,
        Sub_Category,
        SUM(Sales) as TotalSales,
        SUM(Profit) as TotalProfit,
        COUNT(DISTINCT Order_ID) as OrderCount
    FROM orders
    GROUP BY Product_ID, Product_Name, Category, Sub_Category
    ORDER BY TotalSales DESC
    LIMIT 50
    """
    return jsonify(query_to_json(query))

# Route for overall sales summary
@app.route('/api/sales_summary', methods=['GET'])
def sales_summary():
    query = """
    SELECT 
        COUNT(DISTINCT Order_ID) as TotalOrders,
        COUNT(DISTINCT Customer_ID) as TotalCustomers,
        SUM(Sales) as TotalSales,
        SUM(Profit) as TotalProfit,
        (SUM(Profit) / SUM(Sales) * 100) as OverallProfitMargin,
        AVG(Sales) as AverageOrderValue
    FROM orders
    """
    return jsonify(query_to_json(query))

# Route with filtering parameters (can be used for dashboards with filters)
@app.route('/api/filtered_sales', methods=['GET'])
def filtered_sales():
    # Get filter parameters from query string
    region = request.args.get('region', '')
    category = request.args.get('category', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Build the query with filters
    query = """
    SELECT 
        strftime('%Y-%m', Order_Date) as Month,
        Region,
        Category,
        SUM(Sales) as TotalSales,
        SUM(Profit) as TotalProfit
    FROM orders
    WHERE 1=1
    """
    
    params = []
    
    if region:
        query += " AND Region = ?"
        params.append(region)
        
    if category:
        query += " AND Category = ?"
        params.append(category)
        
    if start_date:
        query += " AND Order_Date >= ?"
        params.append(start_date)
        
    if end_date:
        query += " AND Order_Date <= ?"
        params.append(end_date)
    
    query += """
    GROUP BY Month, Region, Category
    ORDER BY Month
    """
    
    return jsonify(query_to_json(query, params=params))

# Create sample data
def create_sample_data():
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if we already have data
        if DataPoint.query.count() == 0:
            # Import sample data
            import datetime
            
            sample_data = [
                DataPoint(category='Sales', value=1200, date=datetime.date(2023, 1, 15)),
                DataPoint(category='Sales', value=1500, date=datetime.date(2023, 2, 15)),
                DataPoint(category='Sales', value=1800, date=datetime.date(2023, 3, 15)),
                DataPoint(category='Costs', value=800, date=datetime.date(2023, 1, 15)),
                DataPoint(category='Costs', value=900, date=datetime.date(2023, 2, 15)),
                DataPoint(category='Costs', value=1000, date=datetime.date(2023, 3, 15)),
            ]
            
            db.session.add_all(sample_data)
            db.session.commit()
            
            print("Sample data created successfully!")

if __name__ == '__main__':
    create_sample_data()  # Create sample data when we run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
