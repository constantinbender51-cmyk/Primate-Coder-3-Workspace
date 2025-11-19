import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from flask import Flask, render_template
import requests
import os

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

def create_plot():
    """Create a matplotlib plot and return as base64 encoded image"""
    conn = sqlite3.connect('chinook.db')
    
    # Read data from database
    df = pd.read_sql_query('SELECT month, revenue, expenses FROM sales', conn)
    conn.close()
    
    # Create plot
    plt.figure(figsize=(10, 6))
    plt.plot(df['month'], df['revenue'], marker='o', label='Revenue', linewidth=2)
    plt.plot(df['month'], df['expenses'], marker='s', label='Expenses', linewidth=2)
    plt.title('Monthly Revenue and Expenses')
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
    
    return plot_url

@app.route('/')
def index():
    """Main page displaying the graph"""
    # Download/create database if needed
    download_database()
    
    # Create the plot
    plot_url = create_plot()
    
    # Get data for table display
    conn = sqlite3.connect('chinook.db')
    df = pd.read_sql_query('SELECT month, revenue, expenses FROM sales', conn)
    conn.close()
    
    # Convert DataFrame to list of dictionaries for template
    data = df.to_dict('records')
    
    return render_template('index.html', plot_url=plot_url, data=data)

if __name__ == '__main__':
    print("Starting web server on port 8000...")
    print("Open http://localhost:8000 in your browser")
    app.run(host='0.0.0.0', port=8000, debug=True)