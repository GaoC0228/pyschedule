#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
加密解密工具
"""

from cryptography.fernet import Fernet
import base64
import os


# 从环境变量获取密钥，如果没有则生成一个
SECRET_KEY = os.getenv('CRYPTO_SECRET_KEY', 'your-secret-key-here-please-change-in-production')

# 确保密钥长度为32字节
def get_fernet_key():
    """获取Fernet密钥"""
    # 将密钥填充或截断到32字节
    key = SECRET_KEY.encode()
    if len(key) < 32:
        key = key + b'0' * (32 - len(key))
    else:
        key = key[:32]
    # Base64编码
    return base64.urlsafe_b64encode(key)


fernet = Fernet(get_fernet_key())


def encrypt_password(password: str) -> str:
    """
    加密密码
    
    Args:
        password: 明文密码
    
    Returns:
        加密后的密码（字符串）
    """
    if not password:
        return None
    
    encrypted = fernet.encrypt(password.encode())
    return encrypted.decode()


def decrypt_password(encrypted_password: str) -> str:
    """
    解密密码
    
    Args:
        encrypted_password: 加密的密码
    
    Returns:
        明文密码
    """
    if not encrypted_password:
        return None
    
    try:
        decrypted = fernet.decrypt(encrypted_password.encode())
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"密码解密失败: {str(e)}")


if __name__ == "__main__":
    # 测试加密解密
    test_password = "my_secret_password_123"
    print(f"原始密码: {test_password}")
    
    encrypted = encrypt_password(test_password)
    print(f"加密后: {encrypted}")
    
    decrypted = decrypt_password(encrypted)
    print(f"解密后: {decrypted}")
    
    assert test_password == decrypted, "加密解密测试失败！"
    print("✓ 加密解密测试通过！")
