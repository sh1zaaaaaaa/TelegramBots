import ssl
import websocket
import asyncio
import json

async def connect_binance(loop, bot, user_liquidation_prices, active_trackers):
    import threading

    def run_websocket():
        ws = websocket.WebSocketApp(
            "wss://fstream.binance.com/ws/!forceOrder@arr",
            on_message=lambda ws, msg: handle_message(ws, msg, loop, bot, user_liquidation_prices, active_trackers),
            on_error=on_error,
            on_close=on_close
        )
        ws.on_open = on_open
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    threading.Thread(target=run_websocket, daemon=True).start()


def on_open(ws):
    print("WebSocket connection opened.")

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"WebSocket connection closed with code: {close_status_code}, message: {close_msg}")

def disconnect_binance():
    global ws
    ws.close()
    ws = None

def handle_message(ws, message, loop, bot, user_liquidation_prices, active_trackers):
    if loop is None:
        print("Main event loop is not initialized.")
        return
    asyncio.run_coroutine_threadsafe(on_message_binance(ws, message, bot, user_liquidation_prices, active_trackers), loop)

async def on_message_binance(ws, message, bot, user_liquidation_prices, active_trackers):
    try:
        data = json.loads(message)

        if "o" in data:
            liquidation = data["o"]
            exchange = "Binance"
            symbol = liquidation.get("s")
            price = float(liquidation.get("p"))
            final_price = float(liquidation.get("ap"))
            qty = float(liquidation.get("q"))
            side = liquidation.get("S")
            roi_loss = round(abs((price * qty) - (final_price * qty)), 2)
            total_loss = round(abs(price * qty), 2)
            pnl_loss = round(abs(100 - (final_price * 100) / price), 2)

            for user_id in active_trackers:
                user_price = user_liquidation_prices.get(user_id)
                if user_price and total_loss >= user_price:
                    alert_message = (
                        f"Alert for {exchange}:\n"
                        f"Symbol: {symbol}\n"
                        f"Side: {side}\n"
                        f"Liquidation Price: {price}\n"
                        f"Quantity: {qty}\n"
                        f"ROI Loss: {roi_loss}\n"
                        f"Total Loss: {total_loss}\n"
                        f"PNL Loss: {pnl_loss}%"
                    )
                    # print(alert_message)
                    await bot.send_message(chat_id=user_id, text=alert_message)
        else:
            print("Unexpected data format. 'o' field not found.")
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
    except Exception as e:
        print(f"Error processing message: {e}")