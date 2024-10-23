import json
import requests
import pandas as pd
import time

URL = "http://fx-trading-game-leicester-challenge.westeurope.azurecontainer.io:443/"
TRADER_ID = "na"
FETCH_INTERVAL = 1  # Fetch data every 60 seconds

class Side:
    BUY = "buy"
    SELL = "sell"


class TradingBot:
    def __init__(self, trader_id, product="EURGBP", short_period=5, long_period=20, risk_percent=0.01, reward_ratio=2):
        self.trader_id = trader_id
        self.product = product
        self.short_period = short_period
        self.long_period = long_period
        self.risk_percent = risk_percent
        self.reward_ratio = reward_ratio
        self.df = pd.DataFrame()  # Holds the price history
        self.last_signal = None  # Keep track of the last signal (buy/sell) to avoid repeated trades
        self.entry_price = None  # Store the price when a trade is executed
        self.stop_loss = None
        self.take_profit = None
    
    # Function to fetch the latest price history (partial update)
    def fetch_latest_price(self):
        api_url = URL + f"/price/{self.product}"
        res = requests.get(api_url)
        if res.status_code == 200:
            data = json.loads(res.content.decode('utf-8'))
            price = data['price']
            timestamp = pd.to_datetime(data['time'])
            return timestamp, price

        return None

    def close_all_trades(self):
        # API endpoint to fetch all open trades
        api_url = URL + f"/positions/{self.trader_id}"
        res = requests.get(api_url)
        if res.status_code == 200:
            open_positions = json.loads(res.content.decode('utf-8'))
            print("Full open positions response:", open_positions)  # Log the full response

            for currency, amount in open_positions.items():
                if amount > 0:  # Check if there's an open position for this currency
                    if currency == "EUR":
                        side_to_close = Side.SELL  # Close sell for EUR
                    elif currency == "GBP":
                        side_to_close = Side.SELL  # Close sell for GBP
                    else:
                        continue  # Skip currencies we don't recognize

                    print(f"Closing {side_to_close} trade for {currency} at current market price.")
                    # Here you should get the current market price to close the trade
                    # For this example, let's assume you call execute_trade to close the position
                    close_price = self.fetch_latest_price()[1]  # Fetch the latest price
                    self.execute_trade(side_to_close)  # Execute the closing trade
        else:
            print("Failed to fetch open positions.")




    # Append the latest price to the dataframe
    def update_price_history(self, timestamp, price):
        new_row = pd.DataFrame({'timestamp': [timestamp], 'price': [price]})
        new_row.set_index('timestamp', inplace=True)
        self.df = pd.concat([self.df, new_row]).last('1000T')  # Keep only the last 100 timestamps (15-minute periods)

    # Calculate the EMAs
    def calculate_emas(self):
        self.df['short_ema'] = self.df['price'].ewm(span=self.short_period, adjust=False).mean()
        self.df['long_ema'] = self.df['price'].ewm(span=self.long_period, adjust=False).mean()

    # Check for buy/sell signals
    def generate_signals(self):
        self.df['buy_signal'] = (self.df['short_ema'] > self.df['long_ema']) & (self.df['short_ema'].shift(1) <= self.df['long_ema'].shift(1))
        self.df['sell_signal'] = (self.df['short_ema'] < self.df['long_ema']) & (self.df['short_ema'].shift(1) >= self.df['long_ema'].shift(1))

        latest_row = self.df.iloc[-1]
        
        if latest_row['buy_signal']:
            return Side.BUY
        elif latest_row['sell_signal']:
            return Side.SELL
        return None

    # Set stop loss and take profit levels based on the entry price
    def set_stop_loss_take_profit(self, entry_price, side):
        if side == Side.BUY:
            self.stop_loss = entry_price * (1 - self.risk_percent)
            self.take_profit = entry_price * (1 + self.risk_percent * self.reward_ratio)
        elif side == Side.SELL:
            self.stop_loss = entry_price * (1 + self.risk_percent)
            self.take_profit = entry_price * (1 - self.risk_percent * self.reward_ratio)

    # Check if the current price meets stop loss or take profit criteria
    def check_exit_conditions(self, price, side):
        if side == Side.BUY:
            if price >= self.take_profit:
                print(f"Take Profit hit! Selling at price: {price}. Profit Target reached.")
                return Side.SELL
            elif price <= self.stop_loss:
                print(f"Stop Loss hit! Selling at price: {price}. Risk Limit reached.")
                return Side.SELL
        elif side == Side.SELL:
            if price <= self.take_profit:
                print(f"Take Profit hit! Buying at price: {price}. Profit Target reached.")
                return Side.BUY
            elif price >= self.stop_loss:
                print(f"Stop Loss hit! Buying at price: {price}. Risk Limit reached.")
                return Side.BUY
        return None


    # Execute a trade
    def execute_trade(self, side):
        api_url = URL + f"/trade/{self.product}"
        data = {"trader_id": self.trader_id, "quantity": 50000, "side": side}
        res = requests.post(api_url, json=data)
        if res.status_code == 200:
            resp_json = json.loads(res.content.decode('utf-8'))
            if resp_json['success']:
                execution_price = float(resp_json['price'])  # Convert to float
                print(f"{side.capitalize()} executed at price: {execution_price}")
                return execution_price  # Return the execution price as a float
        return None


    # Main loop to fetch price data, calculate EMAs, and place trades
    def run(self):
        # Step 0: Close all open trades at the start
        print("Checking for and closing all open trades...")
        self.close_all_trades()

        while True:
            # Step 1: Fetch latest price data
            latest_data = self.fetch_latest_price()
            if latest_data:
                timestamp, price = latest_data
                print(f"Fetched new price: {price} at {timestamp}")
                
                # Step 2: Update the price history with new data
                self.update_price_history(timestamp, price)
                
                # Step 3: Calculate the EMAs
                self.calculate_emas()
                
                # Step 4: Generate buy/sell signals
                signal = self.generate_signals()
                
                # Step 5: Execute trades if a new signal is detected or check exit conditions
                if signal and signal != self.last_signal:
                    print(f"Signal detected: {signal}")
                    executed_price = self.execute_trade(signal)
                    if executed_price:
                        self.entry_price = executed_price
                        self.set_stop_loss_take_profit(self.entry_price, signal)
                        self.last_signal = signal
                elif self.entry_price:
                    # Check for exit conditions (stop loss or take profit)
                    exit_signal = self.check_exit_conditions(price, self.last_signal)
                    if exit_signal:
                        executed_price = self.execute_trade(exit_signal)
                        if executed_price:
                            # Reset after exiting the trade
                            self.entry_price = None
                            self.stop_loss = None
                            self.take_profit = None
                            self.last_signal = None
                else:
                    print("No trade executed. Monitoring continues...")
            else:
                print("Failed to fetch price. Retrying...")
            
            # Step 6: Wait before fetching new data
            time.sleep(FETCH_INTERVAL)



# Initialize and run the bot
if __name__ == "__main__":
    bot = TradingBot(trader_id=TRADER_ID)
    bot.run()
