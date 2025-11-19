import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from flask import Flask, render_template
import requests
import os
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder

app = Flask(__name__)

def download_database():
    """Download a sample SQLite database"""
    url = "https://www.sqlitetutorial.net/wp-content/uploads/2018/03/chinook.zip"
    local_file = "chinook.db"
    
    if not os.path.exists(local_file):
        print("Downloading database...")
        # For this example, we'll create a simple database instead
        create_sample_database()
    
    return local_file

def create_sample_database():
    """Create a sample database with some data"""
    conn = sqlite3.connect('chinook.db')
    cursor = conn.cursor()
    
    # Create a sample table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY,
            month TEXT,
            revenue REAL,
            expenses REAL
        )
    ''')
    
    # Insert sample data
    sample_data = [
        ('January', 15000, 8000),
        ('February', 18000, 8500),
        ('March', 22000, 9000),
        ('April', 19000, 8200),
        ('May', 25000, 9500),
        ('June', 28000, 10000)
    ]
    
    cursor.executemany('INSERT INTO sales (month, revenue, expenses) VALUES (?, ?, ?)', sample_data)
    conn.commit()
    conn.close()

def predict_next_quarter_revenue(df):
    """Use linear regression to predict next quarter's revenue"""
    # Convert months to numerical values
    months = ['January', 'February', 'March', 'April', 'May', 'June', 
              'July', 'August', 'September', 'October', 'November', 'December']
    
    # Create numerical mapping for months
    month_to_num = {month: i+1 for i, month in enumerate(months)}
    
    # Prepare data for training
    X = np.array([month_to_num[month] for month in df['month']]).reshape(-1, 1)
    y = df['revenue'].values
    
    # Train linear regression model
    model = LinearRegression()
    model.fit(X, y)
    
    # Predict next quarter (next 3 months)
    next_months_nums = [len(df) + 1, len(df) + 2, len(df) + 3]
    next_months_names = [months[(len(df) + i) % 12] for i in range(3)]
    predictions = model.predict(np.array(next_months_nums).reshape(-1, 1))
    
    # Create prediction data
    predictions_data = []
    for i, (month, pred) in enumerate(zip(next_months_names, predictions)):
        predictions_data.append({
            'month': month,
            'revenue': float(pred),
            'expenses': float(df['expenses'].mean() * 1.05),  # Estimate expenses
            'is_prediction': True
        })
    
    return predictions_data, model

def create_plot():
    """Create a matplotlib plot with actual data and predictions"""
    conn = sqlite3.connect('chinook.db')
    
    # Read data from database
    df = pd.read_sql_query('SELECT month, revenue, expenses FROM sales', conn)
    conn.close()
    
    # Get predictions
    predictions_data, model = predict_next_quarter_revenue(df)
    
    # Create plot
    plt.figure(figsize=(12, 7))
    
    # Plot actual data
    plt.plot(df['month'], df['revenue'], marker='o', label='Actual Revenue', 
             linewidth=2, color='blue', markersize=6)
    plt.plot(df['month'], df['expenses'], marker='s', label='Actual Expenses', 
             linewidth=2, color='red', markersize=6)
    
    # Prepare prediction data
    pred_months = [pred['month'] for pred in predictions_data]
    pred_revenue = [pred['revenue'] for pred in predictions_data]
    pred_expenses = [pred['expenses'] for pred in predictions_data]
    
    # Plot predictions
    plt.plot(pred_months, pred_revenue, marker='o', label='Predicted Revenue', 
             linewidth=2, color='lightblue', linestyle='--', markersize=6)
    plt.plot(pred_months, pred_expenses, marker='s', label='Predicted Expenses', 
             linewidth=2, color='lightcoral', linestyle='--', markersize=6)
    
    # Add vertical line to separate actual from predicted
    last_actual_month = df['month'].iloc[-1]
    plt.axvline(x=last_actual_month, color='gray', linestyle=':', alpha=0.7)
    plt.text(last_actual_month, plt.ylim()[1] * 0.9, 'Prediction Start', 
             rotation=90, verticalalignment='top', fontsize=10)
    
    plt.title('Monthly Revenue and Expenses with Next Quarter Prediction')
    plt.xlabel('Month')
    plt.ylabel('Amount ($)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Convert plot to base64 string
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=100)
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    
    return plot_url, predictions_data

@app.route('/')
def index():
    """Main page displaying the graph"""
    # Download/create database if needed
    download_database()
    
    # Create the plot and get predictions
    plot_url, predictions = create_plot()
    
    # Get data for table display
    conn = sqlite3.connect('chinook.db')
    df = pd.read_sql_query('SELECT month, revenue, expenses FROM sales', conn)
    conn.close()
    
    # Convert DataFrame to list of dictionaries for template
    data = df.to_dict('records')
    
    # Add prediction indicator to actual data
    for item in data:
        item['is_prediction'] = False
    
    # Combine actual data with predictions
    all_data = data + predictions
    
    return render_template('index.html', plot_url=plot_url, data=all_data)

if __name__ == '__main__':
    print("Starting web server on port 8000...")
    print("Open http://localhost:8000 in your browser")
    app.run(host='0.0.0.0', port=8000, debug=True)