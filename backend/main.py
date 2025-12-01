import asyncio
import json
import logging
import secrets
import sys
from datetime import datetime
from typing import Any, Dict, Set

import websockets
from websockets.server import WebSocketServerProtocol

from fhe_service import FHEManager


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("backend.log"),
    ],
)
logger = logging.getLogger(__name__)


fhe_manager = FHEManager(rotation_interval=5 * 60)


connected_clients: Set[WebSocketServerProtocol] = set()
mpc_sessions: Dict[WebSocketServerProtocol, Dict[str, Any]] = {}


def build_server_time() -> Dict[str, Any]:
    """返回统一的服务器时间戳信息。"""
    now = datetime.utcnow()
    return {
        "time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": now.timestamp(),
        "iso_time": now.isoformat(timespec="seconds"),
    }


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

                if msg_type == "GET_FHE_KEY":
                    algorithm = data.get("algorithm", "PAILLIER")
                    try:
                        bundle = fhe_manager.get_key_bundle(algorithm)
                        await websocket.send(
                            json.dumps(
                                {
                                    "type": "FHE_KEY",
                                    **bundle,
                                }
                            )
                        )
                        logger.info("已发送 %s 公钥", bundle["algorithm"])
                    except ValueError as exc:
                        await websocket.send(
                            json.dumps({"type": "FHE_ERROR", "error": str(exc)})
                        )

                elif msg_type == "GET_ALL_FHE_KEYS":
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "FHE_KEYS",
                                "keys": fhe_manager.get_all_key_bundles(),
                            }
                        )
                    )

                elif msg_type == "BATCH_ENCRYPT":
                    algorithm = data.get("algorithm", "PAILLIER")
                    values = data.get("values") or []
                    try:
                        items = fhe_manager.encrypt_batch(algorithm, values)
                        await websocket.send(
                            json.dumps(
                                {
                                    "type": "ENCRYPTED_BATCH",
                                    "algorithm": algorithm,
                                    "items": items,
                                }
                            )
                        )
                        logger.info("完成 %s 批量加密 (%d)", algorithm, len(items))
                    except Exception as exc:  # noqa: BLE001
                        await websocket.send(
                            json.dumps({"type": "FHE_ERROR", "error": str(exc)})
                        )

                elif msg_type == "COMPUTE_FHE":
                    algorithm = data.get("algorithm", "PAILLIER")
                    ciphertexts = data.get("ciphertexts") or []
                    try:
                        result = fhe_manager.compute(algorithm, ciphertexts)
                        await websocket.send(
                            json.dumps(
                                {
                                    "type": "COMPUTE_RESULT",
                                    "algorithm": algorithm,
                                    **result,
                                }
                            )
                        )
                        logger.info("完成 %s 同态计算", algorithm)
                    except Exception as exc:  # noqa: BLE001
                        await websocket.send(
                            json.dumps({"type": "FHE_ERROR", "error": str(exc)})
                        )

                elif msg_type == "GET_SERVER_TIME":
                    payload = {
                        "type": "SERVER_TIME",
                        **build_server_time(),
                        "keys": fhe_manager.get_all_key_bundles(),
                    }
                    await websocket.send(json.dumps(payload))

                elif msg_type == "GET_KEY_STATUS":
                    algorithm = data.get("algorithm")
                    if algorithm:
                        try:
                            info = fhe_manager.get_key_bundle(algorithm)
                            payload = {
                                "type": "KEY_STATUS",
                                "algorithm": algorithm,
                                "key_info": info["key_info"],
                            }
                        except ValueError as exc:
                            payload = {"type": "FHE_ERROR", "error": str(exc)}
                    else:
                        payload = {
                            "type": "KEY_STATUS",
                            "keys": fhe_manager.get_all_key_bundles(),
                        }
                    await websocket.send(json.dumps(payload))

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

                else:
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "UNKNOWN_TYPE",
                                "error": f"不支持的消息类型: {msg_type}",
                            }
                        )
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


async def main() -> None:
    logger.info("=== AliceCrypto 后端服务启动 ===")
    logger.info("正在初始化多算法 FHE 引擎...")

    loop = asyncio.get_running_loop()

    def on_key_rotation() -> None:
        payload = {
            "type": "KEY_ROTATED",
            **build_server_time(),
            "keys": fhe_manager.get_all_key_bundles(),
        }
        logger.info("已轮换 FHE 密钥，通知 %d 个客户端", len(connected_clients))
        asyncio.run_coroutine_threadsafe(broadcast(payload), loop)

    fhe_manager.start_auto_rotation(on_rotate=on_key_rotation)
    logger.info("密钥轮换线程已启动，周期 5 分钟")
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
