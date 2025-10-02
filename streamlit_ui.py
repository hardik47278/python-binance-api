import streamlit as st
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException

# ------------------ Streamlit UI ------------------ #
st.set_page_config(page_title="Binance Futures Testnet Bot", layout="centered")
st.title("📈 Binance Futures Testnet Trading Bot")

# Session state for client
if "client" not in st.session_state:
    st.session_state.client = None

# ------------------ Connect to Binance ------------------ #
st.subheader("🔑 API Connection")
api_key = st.text_input("Enter your Binance Testnet API Key:", type="password")
api_secret = st.text_input("Enter your Binance Testnet API Secret:", type="password")

if st.button("Connect to Testnet"):
    try:
        client = Client(api_key, api_secret)
        client.API_URL = "https://testnet.binancefuture.com/fapi/v1"  # Futures Testnet endpoint
        st.session_state.client = client

        # Fetch balance
        balances = client.futures_account_balance()
        usdt_balance = next(b["balance"] for b in balances if b["asset"] == "USDT")
        st.success(f"✅ Connected! Testnet USDT Balance: {usdt_balance}")
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")

# ------------------ Place Order ------------------ #
if st.session_state.client:
    st.subheader("📌 Place Order")

    symbol = st.text_input("Symbol (e.g., BTCUSDT)", "BTCUSDT").upper()
    side = st.selectbox("Side", ["BUY", "SELL"])
    order_type = st.selectbox("Order Type", ["MARKET", "LIMIT"])
    quantity = st.number_input("Quantity", min_value=0.0001, value=0.001, format="%.6f")

    price = None
    if order_type == "LIMIT":
        price = st.number_input("Price", min_value=1.0, value=30000.0, format="%.2f")

    if st.button("Submit Order"):
        client = st.session_state.client
        try:
            # Current market price
            current_price = float(client.futures_symbol_ticker(symbol=symbol)["price"])

            # Check balance
            balance = float(next(b["balance"] for b in client.futures_account_balance() if b["asset"] == "USDT"))
            notional = (price if price else current_price) * quantity
            min_notional = 100  # Binance Futures rule
            required_margin = notional / 20  # assuming 20x leverage

            if notional < min_notional:
                st.error(f"❌ Notional too small: {notional:.2f} USDT (min {min_notional})")
            elif required_margin > balance:
                st.error(f"❌ Margin insufficient. Balance={balance}, required≈{required_margin:.2f}")
            else:
                params = {"symbol": symbol, "side": side, "type": order_type, "quantity": quantity}
                if order_type == "LIMIT":
                    params["price"] = price
                    params["timeInForce"] = "GTC"

                order = client.futures_create_order(**params)
                st.success("✅ Order placed successfully!")
                st.json(order)

        except BinanceAPIException as e:
            st.error(f"❌ Binance API Error: {e}")
        except BinanceOrderException as e:
            st.error(f"❌ Binance Order Error: {e}")
        except Exception as e:
            st.error(f"❌ Unexpected Error: {e}")
