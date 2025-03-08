from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
import pandas as pd

# Create Flask application
app = Flask(__name__)

# Configure database connection
# Replace with your actual database connection string
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
    app.run(debug=True)
