import asyncio
import json
import logging
import secrets
import sys
from datetime import datetime
from typing import Any, Dict, Set

import websockets
from websockets.server import WebSocketServerProtocol

import crypto_utils
import database
import paillier_service


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("backend.log"),
    ],
)
logger = logging.getLogger(__name__)


database.init_db()
crypto_manager = crypto_utils.CryptoManager()


connected_clients: Set[WebSocketServerProtocol] = set()
mpc_sessions: Dict[WebSocketServerProtocol, Dict[str, Any]] = {}


async def broadcast(message: Dict[str, Any]) -> None:
    """向所有已连接客户端广播消息。"""
    if not connected_clients:
        return

    payload = json.dumps(message)
    tasks = []
    for client in list(connected_clients):
        if client.closed:
            connected_clients.discard(client)
            continue
        tasks.append(client.send(payload))

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def handler(websocket: WebSocketServerProtocol) -> None:
    client_addr = websocket.remote_address
    logger.info("新连接: %s", client_addr)

    connected_clients.add(websocket)

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type")

                if msg_type == "HANDSHAKE_INIT":
                    client_pub = data.get("publicKey")
                    logger.info("收到握手请求")

                    server_pub = crypto_manager.get_public_key_b64(websocket)

                    if crypto_manager.handle_handshake(websocket, client_pub):
                        await websocket.send(
                            json.dumps({"type": "HANDSHAKE_REPLY", "publicKey": server_pub})
                        )
                        logger.info("握手完成")
                    else:
                        await websocket.send(
                            json.dumps(
                                {
                                    "type": "HANDSHAKE_ERROR",
                                    "error": "密钥协商失败",
                                }
                            )
                        )

                elif msg_type == "CHAT_MESSAGE":
                    content_enc = data.get("content")
                    iv = data.get("iv")

                    try:
                        plaintext = crypto_manager.decrypt_message(websocket, iv, content_enc)
                        logger.info("收到密文，解密内容: %s", plaintext)

                        database.save_message("Alice", content_enc, iv)

                        reply_text = f"Server收到: {plaintext} (From Python)"
                        encrypted_reply = crypto_manager.encrypt_reply(websocket, reply_text)

                        await websocket.send(
                            json.dumps(
                                {
                                    "type": "CHAT_REPLY",
                                    "sender": "Bob (Server)",
                                    "content": encrypted_reply["content"],
                                    "iv": encrypted_reply["iv"],
                                }
                            )
                        )
                    except Exception as exc:  # noqa: BLE001
                        logger.error("解密或回复失败: %s", exc)

                elif msg_type == "GET_SERVER_TIME":
                    now = datetime.now()
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "SERVER_TIME",
                                "time": now.strftime("%Y-%m-%d %H:%M:%S"),
                                "timestamp": now.timestamp(),
                            }
                        )
                    )

                elif msg_type == "GET_PAILLIER_KEY":
                    logger.info("前端请求 Paillier 公钥")
                    key_data = paillier_service.get_public_key_with_info()

                    await websocket.send(
                        json.dumps(
                            {
                                "type": "PAILLIER_KEY",
                                **key_data,
                            }
                        )
                    )
                    logger.info("已发送 Paillier 公钥")

                elif msg_type == "GET_KEY_STATUS":
                    key_info = paillier_service.get_key_info()

                    await websocket.send(
                        json.dumps(
                            {
                                "type": "KEY_STATUS",
                                "key_info": key_info,
                            }
                        )
                    )

                elif msg_type == "ENCRYPT_VALUE":
                    value = data.get("value")
                    logger.info("收到加密请求: %s", value)

                    ciphertext = paillier_service.encrypt_value(int(value))

                    await websocket.send(
                        json.dumps(
                            {
                                "type": "ENCRYPTED_VALUE",
                                "ciphertext": ciphertext,
                                "original": str(value),
                            }
                        )
                    )

                elif msg_type == "DECRYPT_VALUE":
                    ciphertext = data.get("ciphertext")
                    logger.info("收到解密请求")

                    try:
                        plaintext = paillier_service.decrypt_value(ciphertext)
                        await websocket.send(
                            json.dumps({"type": "DECRYPTED_VALUE", "plaintext": plaintext})
                        )
                    except Exception as exc:  # noqa: BLE001
                        await websocket.send(
                            json.dumps({"type": "DECRYPT_ERROR", "error": str(exc)})
                        )

                elif msg_type == "COMPUTE_SUM":
                    logger.info("收到同态计算请求 (自带公钥)")
                    pub_key = data.get("pub_key")
                    values = data.get("values")

                    result_cipher = paillier_service.compute_homomorphic_sum(
                        pub_key["n"],
                        pub_key["g"],
                        values,
                    )

                    await websocket.send(
                        json.dumps({"type": "COMPUTE_RESULT", "result": result_cipher})
                    )

                elif msg_type == "COMPUTE_SUM_SERVER_KEY":
                    logger.info("收到同态计算请求（服务端密钥）")
                    ciphertexts = data.get("values")
                    return_plaintext = data.get("return_plaintext", True)

                    result = paillier_service.compute_with_server_key(
                        ciphertexts,
                        return_plaintext=return_plaintext,
                    )

                    if result:
                        await websocket.send(
                            json.dumps({"type": "COMPUTE_RESULT_SERVER_KEY", **result})
                        )
                    else:
                        await websocket.send(
                            json.dumps({"type": "COMPUTE_ERROR", "error": "计算失败"})
                        )

                elif msg_type == "MPC_GENERATE_SECRET":
                    secret = secrets.randbelow(9_000_000) + 1_000_000
                    mpc_sessions[websocket] = {
                        "secret": secret,
                        "generated_at": datetime.utcnow().isoformat(),
                    }
                    logger.info("为 %s 生成 MPC 密钥", client_addr)

                    await websocket.send(
                        json.dumps(
                            {
                                "type": "MPC_SECRET_GENERATED",
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )
                    )

                elif msg_type == "MPC_COMPARE_INIT":
                    try:
                        alice_value = int(data.get("value"))
                    except (TypeError, ValueError):
                        await websocket.send(
                            json.dumps(
                                {
                                    "type": "MPC_ERROR",
                                    "error": "无效的输入值",
                                }
                            )
                        )
                        continue

                    session = mpc_sessions.get(websocket)
                    if not session:
                        await websocket.send(
                            json.dumps(
                                {
                                    "type": "MPC_ERROR",
                                    "error": "服务器尚未生成 Bob 的秘密，请先生成",
                                }
                            )
                        )
                        continue

                    bob_secret = session["secret"]

                    if alice_value > bob_secret:
                        compare_result = "Alice is Richer"
                    elif alice_value < bob_secret:
                        compare_result = "Bob is Richer"
                    else:
                        compare_result = "Equal Wealth"

                    await websocket.send(
                        json.dumps(
                            {
                                "type": "MPC_COMPARE_RESULT",
                                "result": compare_result,
                            }
                        )
                    )
                    logger.info(
                        "完成百万富翁协议: Alice=%s, Bob=%s, 结果=%s",
                        alice_value,
                        bob_secret,
                        compare_result,
                    )

            except json.JSONDecodeError:
                logger.error("接收到非 JSON 数据")
            except Exception as exc:  # noqa: BLE001
                logger.exception("处理消息时发生未知错误: %s", exc)

    except websockets.exceptions.ConnectionClosed:
        logger.info("连接断开: %s", client_addr)
    finally:
        connected_clients.discard(websocket)
        mpc_sessions.pop(websocket, None)
        crypto_manager.remove_client(websocket)


async def main() -> None:
    logger.info("=== AliceCrypto 后端服务启动 ===")
    logger.info("正在初始化 Paillier 密钥对 (2048 bit)...")
    paillier_service.init_paillier_keys(2048)

    loop = asyncio.get_running_loop()

    def on_key_rotation() -> None:
        payload = {"type": "KEY_ROTATED", **paillier_service.get_public_key_with_info()}
        logger.info("Paillier 密钥已轮换，通知 %d 个客户端", len(connected_clients))
        asyncio.run_coroutine_threadsafe(broadcast(payload), loop)

    paillier_service.start_key_rotation(key_size=2048, interval=5 * 60, on_rotate=on_key_rotation)
    logger.info("Paillier 密钥系统初始化完成")
    logger.info("监听端口: 8080 (0.0.0.0)")

    try:
        async with websockets.serve(handler, "0.0.0.0", 8080):
            await asyncio.Future()
    except Exception as exc:  # noqa: BLE001
        logger.critical("服务器启动失败: %s", exc)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务器手动停止")
