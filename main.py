import asyncio
import random
import json
import time
import uuid
from loguru import logger
from websockets_proxy import Proxy, proxy_connect

async def connect_to_wss(proxy_url, user_id):
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, proxy_url))
    logger.info(device_id)
    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            custom_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            uri = "wss://proxy.wynd.network:4650/"
            server_hostname = "proxy.wynd.network"
            proxy = Proxy.from_url(proxy_url)

            # Set ssl=None to bypass SSL verification
            async with proxy_connect(uri, proxy=proxy, ssl=None, server_hostname=server_hostname,
                                     extra_headers=custom_headers) as websocket:
                async def send_ping():
                    while True:
                        send_message = json.dumps(
                            {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                        logger.debug(send_message)
                        await websocket.send(send_message)
                        await asyncio.sleep(20)

                await asyncio.sleep(1)
                asyncio.create_task(send_ping())

                while True:
                    response = await websocket.recv()
                    message = json.loads(response)
                    logger.info(message)
                    if message.get("action") == "AUTH":
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": custom_headers['User-Agent'],
                                "timestamp": int(time.time()),
                                "device_type": "extension",
                                "version": "2.5.0"
                            }
                        }
                        logger.debug(auth_response)
                        await websocket.send(json.dumps(auth_response))

                    elif message.get("action") == "PONG":
                        pong_response = {"id": message["id"], "origin_action": "PONG"}
                        logger.debug(pong_response)
                        await websocket.send(json.dumps(pong_response))
        except Exception as e:
            logger.error(e)
            logger.error(proxy_url)


async def main():
    # TODO 修改user_id
    _user_id = '2oWHDE7vLdgBLi0xXHGPEoeL5xc'
    
    # Load proxies from proxylist.txt and format them as socks5 or http URLs
    with open("proxylist.txt", "r") as f:
        proxy_list = []
        for line in f:
            line = line.strip()
            if not line.startswith("socks5://") and not line.startswith("http://"):
                # Default to socks5 if no protocol is specified
                line = f"socks5://{line}"
            proxy_list.append(line)

    tasks = [asyncio.ensure_future(connect_to_wss(proxy, _user_id)) for proxy in proxy_list]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    # Run the main function
    asyncio.run(main())
