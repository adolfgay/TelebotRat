#это все ии
import asyncio
import logging
import os
import threading
import time
import urllib.request
from aiohttp import web, WSMsgType

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Глобальные переменные
sender_socket = None
listener_sockets = set()

# Обработчик для HTML страницы
async def handle_http(request):
    try:
        return web.FileResponse('./websocket_audio_client.html')
    except FileNotFoundError:
        return web.FileResponse('./websocket_audio_client.html')
    except Exception as e:
        logger.error(f"Error serving HTML: {e}")
        return web.Response(status=500, text="Internal Server Error")

# Обработчик WebSocket
async def handle_websocket(request):
    global sender_socket, listener_sockets
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    is_sender = False

    # Определяем роль
    if sender_socket is None:
        sender_socket = ws
        is_sender = True
        logger.info("Sender connected.")
    else:
        listener_sockets.add(ws)
        logger.info(f"Listener connected. Total listeners: {len(listener_sockets)}")

    try:
        async for msg in ws:
            if msg.type == WSMsgType.BINARY:
                if is_sender and msg.data:
                    # Отправляем данные всем слушателям
                    disconnected = set()
                    # logger.info(f"Received {len(msg.data)} bytes from sender.") # Для отладки
                    for listener in list(listener_sockets):
                        try:
                             if not listener.closed:
                                 await listener.send_bytes(msg.data)
                             else:
                                 disconnected.add(listener)
                        except Exception as e:
                             logger.error(f"Error sending to listener {listener}: {e}")
                             disconnected.add(listener)

                    if disconnected:
                        listener_sockets -= disconnected
                        logger.info(f"Removed {len(disconnected)} disconnected listeners.")

            elif msg.type == WSMsgType.ERROR:
                logger.error(f'WebSocket connection closed with exception {ws.exception()}')
            elif msg.type == WSMsgType.TEXT:
                 logger.info(f"Received text message (ignored): {msg.data}")


    except Exception as e:
         logger.error(f"WebSocket handler error: {e}")
    finally:
        logger.info("WebSocket connection closed.")
        if is_sender and sender_socket == ws:
            sender_socket = None
            logger.info("Sender disconnected.")
        elif ws in listener_sockets:
            listener_sockets.remove(ws)
            logger.info(f"Listener disconnected. Total listeners: {len(listener_sockets)}")

    return ws

# Функция keep-alive
def keep_alive():
    def ping_self():
        while True:
            try:
                replit_slug = os.environ.get("REPL_SLUG", "")
                replit_owner = os.environ.get("REPL_OWNER", "")
                replit_id = os.environ.get("REPL_ID", "")

                if replit_slug and replit_owner:
                    url = f"https://{replit_slug}.{replit_owner}.repl.co"
                elif replit_id:
                    url = f"https://{replit_id}.id.repl.co"
                else:
                    # Попытка угадать URL (может не сработать)
                    host = os.environ.get("REPLIT_CLI_API_HOSTNAME") or "localhost:8080"
                    url = f"http://{host}"

                urllib.request.urlopen(url, timeout=10)
                logger.info(f"Keep-alive ping successful to {url}")
            except Exception as e:
                logger.error(f"Keep-alive ping failed: {e}")
            time.sleep(300) # Пинг каждые 5 минут

    t = threading.Thread(target=ping_self, daemon=True)
    t.start()
    logger.info("Keep-alive thread started.")


# Основная функция запуска
async def main():
    keep_alive() # Запускаем поток keep-alive

    app = web.Application()
    app.add_routes([
        web.get('/', handle_http),
        web.get('/ws', handle_websocket) # Путь для WebSocket
    ])

    runner = web.AppRunner(app)
    await runner.setup()
    # Используем порт 8080, который доступен в Replit
    site = web.TCPSite(runner, '0.0.0.0', 8080) 
    logger.info("Server starting on http://0.0.0.0:8080")
    await site.start()

    # Бесконечный цикл для поддержания работы сервера
    await asyncio.Event().wait()

if __name__ == '__main__':
    # Установка зависимостей при первом запуске
    if not os.path.exists('.dependencies-installed'):
        print("Installing dependencies: aiohttp...")
        os.system('pip install aiohttp')
        with open('.dependencies-installed', 'w') as f: f.write('done')
        print("Dependencies installed.")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped manually.")
