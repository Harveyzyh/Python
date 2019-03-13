#AES-demo

import base64
from Crypto.Cipher import AES

'''
采用AES对称加密算法
'''


# str不是16的倍数那就补足为16的倍数
def add_to_16(value):
	while len(value) % 16 != 0:
		value += '\0'
	return str.encode(value)  # 返回bytes


# 加密方法
def encrypt_oracle():
	# 秘钥
	key = 'Venushui'
	# 待加密文本
	text = r'"Uid": "001114", "Mode": "Complete", "Parameter": "JH201812281329460001", "Data": "", "RowCount": "4"'
	# 初始化加密器
	aes = AES.new(add_to_16(key), AES.MODE_ECB)
	# 先进行aes加密
	encrypt_aes = aes.encrypt(add_to_16(text))
	# 用base64转成字符串形式
	encrypted_text = str(base64.encodebytes(encrypt_aes), encoding='utf-8')  # 执行加密并转码返回bytes
	print(encrypted_text)
	
	
# 解密方法
def decrypt_oralce():
	# 秘钥
	key = 'Venushui'
	# 密文
	text = 'ZUFr9BXuaB/GDz04XOXFrpKfMW4Smn8YVF8EXEHB2p9eREX1WcBhi/lOsggdsk9WWXEyygbp/S7EjYMj3dkxhKTIlM26zVt4CvPKPdutc5GpNnZtShQWLbuMNcgBbREWUT7IVHteA4LwLgMU34EFIw=='
	# 初始化加密器
	aes = AES.new(add_to_16(key), AES.MODE_ECB)
	# 优先逆向解密base64成bytes
	base64_decrypted = base64.decodebytes(text.encode(encoding='utf-8'))
	# 执行解密密并转码返回str
	decrypted_text = str(aes.decrypt(base64_decrypted), encoding='utf-8').replace('\0', '')
	print(decrypted_text)


if __name__ == '__main__':
	# encrypt_oracle()
	decrypt_oralce()
