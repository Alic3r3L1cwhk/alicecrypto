import base64
import os
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class CryptoManager:
    def __init__(self):
        # 生成服务器的临时 ECDH 密钥对 (NIST P-256 曲线)
        self.server_private_key = ec.generate_private_key(ec.SECP256R1())
        self.server_public_key = self.server_private_key.public_key()
        # 存储客户端连接对应的共享密钥: { websocket_obj: aes_key_bytes }
        self.client_keys = {}

    def get_public_key_b64(self):
        """导出服务器公钥为 Base64 字符串 (SPKI 格式，供前端 WebCrypto 使用)"""
        pub_bytes = self.server_public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return base64.b64encode(pub_bytes).decode('utf-8')

    def handle_handshake(self, websocket, client_pub_b64):
        """处理来自客户端的公钥，计算共享密钥"""
        try:
            # 1. 解码客户端公钥
            client_pub_bytes = base64.b64decode(client_pub_b64)
            client_public_key = serialization.load_der_public_key(client_pub_bytes)

            # 2. ECDH 交换，得到共享秘密 (Shared Secret)
            shared_secret = self.server_private_key.exchange(ec.ECDH(), client_public_key)

            # 3. 使用 HKDF 派生出 AES 密钥 (32字节 = 256位)
            # 必须与前端 WebCrypto 的 deriveKey 参数完全一致
            aes_key = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=None, # 前端使用了空 salt
                info=b'handshake data', # 前端使用了这个 info 字符串
            ).derive(shared_secret)

            # 4. 存储密钥
            self.client_keys[websocket] = aes_key
            print(f"[Crypto] 与客户端建立安全连接，AES 密钥已生成")
            return True
        except Exception as e:
            print(f"[Crypto] 密钥协商失败: {e}")
            return False

    def decrypt_message(self, websocket, iv_b64, ciphertext_b64):
        """使用协商好的密钥解密消息"""
        if websocket not in self.client_keys:
            raise Exception("未找到该连接的密钥，请先握手")
        
        key = self.client_keys[websocket]
        aesgcm = AESGCM(key)
        
        iv = base64.b64decode(iv_b64)
        ciphertext = base64.b64decode(ciphertext_b64)
        
        # AES-GCM 解密
        plaintext_bytes = aesgcm.decrypt(iv, ciphertext, None)
        return plaintext_bytes.decode('utf-8')

    def encrypt_reply(self, websocket, plaintext_text):
        """加密回复消息"""
        if websocket not in self.client_keys:
            raise Exception("未找到该连接的密钥")

        key = self.client_keys[websocket]
        aesgcm = AESGCM(key)
        
        # 生成随机 IV (12字节)
        iv = os.urandom(12)
        plaintext_bytes = plaintext_text.encode('utf-8')
        
        # 加密
        ciphertext = aesgcm.encrypt(iv, plaintext_bytes, None)
        
        return {
            'content': base64.b64encode(ciphertext).decode('utf-8'),
            'iv': base64.b64encode(iv).decode('utf-8')
        }

    def remove_client(self, websocket):
        if websocket in self.client_keys:
            del self.client_keys[websocket]
