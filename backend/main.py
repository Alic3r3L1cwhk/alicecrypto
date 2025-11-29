import asyncio
import websockets
import json
import logging
import sys

# 导入我们的自定义模块
import database
import crypto_utils
import paillier_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('backend.log')
    ]
)
logger = logging.getLogger(__name__)

# 初始化
database.init_db()
crypto_manager = crypto_utils.CryptoManager()

async def handler(websocket):
    client_addr = websocket.remote_address
    logger.info(f"新连接: {client_addr}")
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type')

                # === 功能 1: 安全聊天 (Diffie-Hellman + AES) ===
                
                if msg_type == 'HANDSHAKE_INIT':
                    # 1. 收到前端公钥
                    client_pub = data.get('publicKey')
                    logger.info("收到握手请求...")
                    
                    if crypto_manager.handle_handshake(websocket, client_pub):
                        # 2. 回复服务端公钥
                        server_pub = crypto_manager.get_public_key_b64()
                        await websocket.send(json.dumps({
                            'type': 'HANDSHAKE_REPLY',
                            'publicKey': server_pub
                        }))
                        logger.info("握手完成，已发送服务端公钥")

                elif msg_type == 'CHAT_MESSAGE':
                    # 3. 收到加密消息
                    content_enc = data.get('content')
                    iv = data.get('iv')
                    
                    try:
                        # 解密
                        plaintext = crypto_manager.decrypt_message(websocket, iv, content_enc)
                        logger.info(f"收到密文，解密内容: {plaintext}")
                        
                        # 存库
                        database.save_message("Alice", content_enc, iv)
                        
                        # 自动回复 (加密)
                        reply_text = f"Server收到: {plaintext} (From Python)"
                        encrypted_reply = crypto_manager.encrypt_reply(websocket, reply_text)
                        
                        await websocket.send(json.dumps({
                            'type': 'CHAT_REPLY',
                            'sender': 'Bob (Server)',
                            'content': encrypted_reply['content'],
                            'iv': encrypted_reply['iv']
                        }))
                    except Exception as e:
                        logger.error(f"解密或回复失败: {e}")

                # === 功能 2: 隐私计算 (Paillier) ===
                
                elif msg_type == 'COMPUTE_SUM':
                    logger.info("收到同态计算请求")
                    pub_key = data.get('pub_key')
                    values = data.get('values')
                    
                    result_cipher = paillier_service.compute_homomorphic_sum(
                        pub_key['n'], 
                        pub_key['g'], 
                        values
                    )
                    
                    logger.info(f"计算完成，结果密文: {result_cipher}")
                    
                    await websocket.send(json.dumps({
                        'type': 'COMPUTE_RESULT',
                        'result': result_cipher
                    }))

            except json.JSONDecodeError:
                logger.error("接收到非 JSON 数据")
            except Exception as e:
                logger.error(f"处理消息时发生未知错误: {e}")

    except websockets.exceptions.ConnectionClosed:
        logger.info(f"连接断开: {client_addr}")
    finally:
        crypto_manager.remove_client(websocket)

async def main():
    # 监听 0.0.0.0 允许外部连接
    logger.info("=== AliceCrypto 后端服务启动 ===")
    logger.info("监听端口: 8080 (0.0.0.0)")
    
    try:
        async with websockets.serve(handler, "0.0.0.0", 8080):
            await asyncio.Future()  # run forever
    except Exception as e:
        logger.critical(f"服务器启动失败: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务器手动停止")
