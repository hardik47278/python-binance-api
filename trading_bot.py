import logging
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException


logging.basicConfig(
    filename='trading_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class BasicBot:
    def __init__(self, api_key, api_secret, testnet=True):
        self.client = Client(api_key, api_secret)
        if testnet:
            self.client.API_URL = 'https://testnet.binancefuture.com/fapi/v1'
        logging.info("Bot initialized. Testnet=%s", testnet)

    def place_order(self, symbol, side, order_type, quantity, price=None):
        """Place a market or limit futures order safely."""
        try:
            
            info = self.client.futures_exchange_info()
            symbol_info = next((s for s in info['symbols'] if s['symbol'] == symbol), None)
            if not symbol_info:
                print("❌ Invalid symbol")
                return

           
            current_price = float(self.client.futures_symbol_ticker(symbol=symbol)['price'])

            
            if order_type == 'LIMIT':
                if price is None:
                    price = current_price
                notional = quantity * price
                min_notional = 100  
                if notional < min_notional:
                    print(f"❌ Order notional too small: {notional} USDT (min {min_notional})")
                    return

           
            balance = float(next(b['balance'] for b in self.client.futures_account_balance() if b['asset'] == 'USDT'))
        
            required_margin = (quantity * (price if price else current_price)) / 20
            if required_margin > balance:
                print(f"❌ Margin insufficient. Balance={balance}, required≈{required_margin}")
                return

            
            params = {'symbol': symbol, 'side': side, 'type': order_type, 'quantity': quantity}
            if order_type == 'LIMIT':
                params['price'] = price
                params['timeInForce'] = 'GTC'

           
            order = self.client.futures_create_order(**params)
            logging.info("Order placed: %s", order)
            print("✅ Order placed successfully:", order)
            return order

        except BinanceAPIException as e:
            logging.error("Binance API Exception: %s", e)
            print("❌ Binance API Error:", e)
        except BinanceOrderException as e:
            logging.error("Binance Order Exception: %s", e)
            print("❌ Binance Order Error:", e)
        except Exception as e:
            logging.error("Unexpected error: %s", e)
            print("❌ Unexpected error:", e)


def get_user_input(bot):
    """Get and validate CLI input from the user."""
    symbol = input("Enter Symbol (e.g., BTCUSDT): ").upper()
    if not symbol.isalnum():
        print("❌ Invalid symbol format")
        return None

    side = input("Enter Side (BUY/SELL): ").upper()
    if side not in ['BUY', 'SELL']:
        print("❌ Side must be BUY or SELL")
        return None

    order_type = input("Order Type (MARKET/LIMIT): ").upper()
    if order_type not in ['MARKET', 'LIMIT']:
        print("❌ Order type must be MARKET or LIMIT")
        return None

    try:
        quantity = float(input("Quantity: "))
        if quantity <= 0:
            print("❌ Quantity must be positive")
            return None
    except ValueError:
        print("❌ Quantity must be a number")
        return None

    price = None
    if order_type == 'LIMIT':
        try:
            price = float(input("Price (enter 0 for current market price): "))
            if price <= 0:
          
                price = float(bot.client.futures_symbol_ticker(symbol=symbol)['price'])
                print(f"ℹ Using current market price: {price}")
        except ValueError:
            print("❌ Price must be a number")
            return None

    return symbol, side, order_type, quantity, price


def main():
    print("=== Binance Futures Testnet Trading Bot ===")
    api_key = input("Enter your Binance Testnet API Key: ").strip()
    api_secret = input("Enter your Binance Testnet API Secret: ").strip()
    bot = BasicBot(api_key, api_secret, testnet=True)

    while True:
        user_input = get_user_input(bot)
        if user_input:
            symbol, side, order_type, quantity, price = user_input
            bot.place_order(symbol, side, order_type, quantity, price)

        cont = input("\nDo you want to place another order? (y/n): ").lower()
        if cont != 'y':
            print("Exiting bot. Check 'trading_bot.log' for details.")
            break

if __name__ == "__main__":
    main()
