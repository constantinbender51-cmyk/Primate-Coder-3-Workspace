from flask import Flask, render_template, jsonify
import pandas as pd
from binance.client import Client
import ta
from datetime import datetime
import threading
import time

app = Flask(__name__)

# Global variable to store the data
btc_data = None
data_lock = threading.Lock()

class BinanceDataFetcher:
    def __init__(self):
        self.client = Client()
        
    def fetch_historical_data(self, symbol='BTCUSDT', start_date='2018-01-01'):
        """Fetch historical BTC data from Binance"""
        try:
            print("Fetching historical BTC data from Binance...")
            
            # Get historical klines data
            klines = self.client.get_historical_klines(
                symbol,
                Client.KLINE_INTERVAL_1DAY,
                start_date
            )
            
            # Convert to DataFrame
            columns = [
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ]
            
            df = pd.DataFrame(klines, columns=columns)
            
            # Convert types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            # Set timestamp as index
            df.set_index('timestamp', inplace=True)
            
            # Keep only necessary columns
            df = df[['open', 'high', 'low', 'close', 'volume']]
            
            print(f"Fetched {len(df)} days of data")
            return df
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None

def calculate_super_trend(df, period=10, multiplier=3):
    """Calculate SuperTrend indicator"""
    try:
        # Calculate ATR
        df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=period)
        
        # Calculate basic upper and lower bands
        hl2 = (df['high'] + df['low']) / 2
        df['upper_band'] = hl2 + (multiplier * df['atr'])
        df['lower_band'] = hl2 - (multiplier * df['atr'])
        
        # Initialize SuperTrend columns
        df['super_trend'] = 0.0
        df['in_uptrend'] = True
        
        # Calculate SuperTrend
        for i in range(1, len(df)):
            current = df.index[i]
            previous = df.index[i-1]
            
            if df.loc[current, 'close'] > df.loc[previous, 'upper_band']:
                df.loc[current, 'in_uptrend'] = True
            elif df.loc[current, 'close'] < df.loc[previous, 'lower_band']:
                df.loc[current, 'in_uptrend'] = False
            else:
                df.loc[current, 'in_uptrend'] = df.loc[previous, 'in_uptrend']
            
            if df.loc[current, 'in_uptrend']:
                df.loc[current, 'super_trend'] = df.loc[current, 'lower_band']
            else:
                df.loc[current, 'super_trend'] = df.loc[current, 'upper_band']
                
        return df
        
    except Exception as e:
        print(f"Error calculating SuperTrend: {e}")
        return df

def update_data():
    """Function to update data periodically"""
    global btc_data
    
    while True:
        try:
            print("Updating BTC data...")
            fetcher = BinanceDataFetcher()
            new_data = fetcher.fetch_historical_data()
            
            if new_data is not None:
                new_data = calculate_super_trend(new_data)
                
                with data_lock:
                    btc_data = new_data
                
                print(f"Data updated successfully at {datetime.now()}")
                
        except Exception as e:
            print(f"Error updating data: {e}")
        
        # Update every hour (3600 seconds)
        time.sleep(3600)

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    """API endpoint to get BTC data with SuperTrend"""
    global btc_data
    
    with data_lock:
        if btc_data is None:
            return jsonify({'error': 'Data not available yet'}), 503
        
        # Prepare data for JSON response
        data = {
            'dates': btc_data.index.strftime('%Y-%m-%d').tolist(),
            'prices': {
                'open': btc_data['open'].tolist(),
                'high': btc_data['high'].tolist(),
                'low': btc_data['low'].tolist(),
                'close': btc_data['close'].tolist()
            },
            'super_trend': btc_data['super_trend'].tolist(),
            'trend_direction': btc_data['in_uptrend'].tolist(),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    return jsonify(data)

@app.route('/api/status')
def status():
    """API endpoint to check data status"""
    global btc_data
    
    with data_lock:
        status_info = {
            'data_available': btc_data is not None,
            'data_points': len(btc_data) if btc_data is not None else 0,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    return jsonify(status_info)

def initialize_data():
    """Initialize data on startup"""
    global btc_data
    
    print("Initializing BTC data...")
    fetcher = BinanceDataFetcher()
    data = fetcher.fetch_historical_data()
    
    if data is not None:
        btc_data = calculate_super_trend(data)
        print("Data initialized successfully")
    else:
        print("Failed to initialize data")

if __name__ == '__main__':
    # Initialize data on startup
    initialize_data()
    
    # Start background update thread
    update_thread = threading.Thread(target=update_data, daemon=True)
    update_thread.start()
    
    # Start Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
