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

# View database schema route
@app.route('/api/schema', methods=['GET'])
def get_schema():
    try:
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all table names
        tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
        cursor.execute(tables_query)
        tables = [table[0] for table in cursor.fetchall()]
        
        schema = {}
        
        # For each table, get its column info
        for table in tables:
            # Skip SQLite internal tables
            if table.startswith('sqlite_'):
                continue
                
            # Get column information
            pragma_query = f"PRAGMA table_info({table});"
            cursor.execute(pragma_query)
            columns = cursor.fetchall()
            
            # Format column info
            column_details = []
            for col in columns:
                column_details.append({
                    'cid': col[0],
                    'name': col[1],
                    'type': col[2],
                    'notnull': col[3],
                    'default_value': col[4],
                    'pk': col[5]
                })
            
            # Get a sample of data (first row)
            try:
                sample_query = f"SELECT * FROM {table} LIMIT 1;"
                cursor.execute(sample_query)
                sample = dict(cursor.fetchone() or {})
            except:
                sample = {}
            
            schema[table] = {
                'columns': column_details,
                'sample_row': sample
            }
        
        # Close the connection
        conn.close()
        
        return jsonify({
            'database': 'sales_data_proper.db',
            'tables': tables,
            'schema': schema
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route for total sales by region
@app.route('/api/sales_by_region', methods=['GET'])
def sales_by_region():
    try:
        query = """
        SELECT region, SUM(sales) as TotalSales
        FROM sales
        GROUP BY region
        ORDER BY TotalSales DESC
        """
        return jsonify(query_to_json(query))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route for total sales by category
@app.route('/api/sales_by_category', methods=['GET'])
def sales_by_category():
    try:
        query = """
        SELECT category, SUM(sales) as TotalSales
        FROM sales
        GROUP BY category
        ORDER BY TotalSales DESC
        """
        return jsonify(query_to_json(query))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route for total sales by subcategory
@app.route('/api/sales_by_subcategory', methods=['GET'])
def sales_by_subcategory():
    try:
        query = """
        SELECT category, sub_category, SUM(sales) as TotalSales
        FROM sales
        GROUP BY category, sub_category
        ORDER BY category, TotalSales DESC
        """
        return jsonify(query_to_json(query))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route for sales trends over time (monthly)
@app.route('/api/monthly_sales', methods=['GET'])
def monthly_sales():
    try:
        query = """
        SELECT 
            strftime('%Y-%m', order_date) as Month,
            SUM(sales) as TotalSales
        FROM sales
        GROUP BY Month
        ORDER BY Month
        """
        return jsonify(query_to_json(query))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route for sales trends over time (quarterly)
@app.route('/api/quarterly_sales', methods=['GET'])
def quarterly_sales():
    try:
        query = """
        SELECT 
            strftime('%Y', order_date) || '-Q' || CAST((strftime('%m', order_date) + 2) / 3 AS TEXT) as Quarter,
            SUM(sales) as TotalSales
        FROM sales
        GROUP BY Quarter
        ORDER BY Quarter
        """
        return jsonify(query_to_json(query))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route for sales trends over time (yearly)
@app.route('/api/yearly_sales', methods=['GET'])
def yearly_sales():
    try:
        query = """
        SELECT 
            strftime('%Y', order_date) as Year,
            SUM(sales) as TotalSales
        FROM sales
        GROUP BY Year
        ORDER BY Year
        """
        return jsonify(query_to_json(query))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route for top products
@app.route('/api/top_products', methods=['GET'])
def top_products():
    try:
        query = """
        SELECT 
            product_id,
            product_name,
            category,
            sub_category,
            SUM(sales) as TotalSales,
            COUNT(DISTINCT order_id) as OrderCount
        FROM sales
        GROUP BY product_id, product_name, category, sub_category
        ORDER BY TotalSales DESC
        LIMIT 50
        """
        return jsonify(query_to_json(query))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route for customer segmentation data
@app.route('/api/customer_segments', methods=['GET'])
def customer_segments():
    try:
        query = """
        SELECT 
            customer_id,
            customer_name,
            segment,
            COUNT(DISTINCT order_id) as OrderCount,
            SUM(sales) as TotalSpent,
            AVG(sales) as AvgOrderValue
        FROM sales
        GROUP BY customer_id, customer_name, segment
        ORDER BY TotalSpent DESC
        """
        return jsonify(query_to_json(query))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route for overall sales summary
@app.route('/api/sales_summary', methods=['GET'])
def sales_summary():
    try:
        query = """
        SELECT 
            COUNT(DISTINCT order_id) as TotalOrders,
            COUNT(DISTINCT customer_id) as TotalCustomers,
            SUM(sales) as TotalSales,
            AVG(sales) as AverageOrderValue
        FROM sales
        """
        return jsonify(query_to_json(query))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route with filtering parameters (can be used for dashboards with filters)
@app.route('/api/filtered_sales', methods=['GET'])
def filtered_sales():
    try:
        # Get filter parameters from query string
        region_param = request.args.get('region', '')
        category_param = request.args.get('category', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        # Build the query with filters
        query = """
        SELECT 
            strftime('%Y-%m', order_date) as Month,
            region,
            category,
            SUM(sales) as TotalSales
        FROM sales
        WHERE 1=1
        """
        
        params = []
        
        if region_param:
            query += " AND region = ?"
            params.append(region_param)
            
        if category_param:
            query += " AND category = ?"
            params.append(category_param)
            
        if start_date:
            query += " AND order_date >= ?"
            params.append(start_date)
            
        if end_date:
            query += " AND order_date <= ?"
            params.append(end_date)
        
        query += """
        GROUP BY Month, region, category
        ORDER BY Month
        """
        
        return jsonify(query_to_json(query, params=params))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to get ship modes
@app.route('/api/ship_modes', methods=['GET'])
def ship_modes():
    try:
        query = """
        SELECT 
            ship_mode,
            COUNT(*) as OrderCount,
            SUM(sales) as TotalSales
        FROM sales
        GROUP BY ship_mode
        ORDER BY TotalSales DESC
        """
        return jsonify(query_to_json(query))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to get sales by state
@app.route('/api/sales_by_state', methods=['GET'])
def sales_by_state():
    try:
        query = """
        SELECT 
            state,
            COUNT(DISTINCT order_id) as OrderCount,
            SUM(sales) as TotalSales
        FROM sales
        GROUP BY state
        ORDER BY TotalSales DESC
        """
        return jsonify(query_to_json(query))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to get sales by city (top cities)
@app.route('/api/sales_by_city', methods=['GET'])
def sales_by_city():
    try:
        limit = request.args.get('limit', '20')
        query = f"""
        SELECT 
            city,
            state,
            COUNT(DISTINCT order_id) as OrderCount,
            SUM(sales) as TotalSales
        FROM sales
        GROUP BY city, state
        ORDER BY TotalSales DESC
        LIMIT {limit}
        """
        return jsonify(query_to_json(query))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Flask route to dashboard.html for d3js visual display
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

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
