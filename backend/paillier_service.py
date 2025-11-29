from phe import paillier, EncryptedNumber

def compute_homomorphic_sum(pub_n_str, pub_g_str, ciphertexts):
    """
    执行同态加法
    :param pub_n_str: 公钥 N (字符串)
    :param pub_g_str: 公钥 G (字符串)
    :param ciphertexts: 密文列表 (字符串列表)
    """
    try:
        # 1. 重建 Paillier 公钥
        # 注意：前端为了演示使用的是小素数，这里的库通常处理大整数
        # 只要前端传来的 N 和 G 符合数学定义，phe 库就能计算
        pub_n = int(pub_n_str)
        public_key = paillier.PaillierPublicKey(n=pub_n)
        
        # 2. 将字符串密文转换为 EncryptedNumber 对象
        encrypted_sum = None
        
        for c_str in ciphertexts:
            c_int = int(c_str)
            # 手动构造 EncryptedNumber，因为我们需要使用前端传来的公钥
            enc_num = EncryptedNumber(public_key, c_int)
            
            if encrypted_sum is None:
                encrypted_sum = enc_num
            else:
                # 同态加法: E(a) + E(b) -> E(a+b)
                encrypted_sum = encrypted_sum + enc_num
        
        # 3. 返回结果密文
        if encrypted_sum:
            return str(encrypted_sum.ciphertext())
        return "0"
        
    except Exception as e:
        print(f"[Paillier] 计算错误: {e}")
        return None
