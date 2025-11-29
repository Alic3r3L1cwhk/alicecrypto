# AliceCrypto 后端服务使用指南

这是一个基于 Python 的 WebSocket 服务器，用于配合前端进行密码学实验（安全通信和同态加密）。

## 1. 环境准备

确保已安装 Python 3.8 或以上版本。

## 2. 安装依赖

在 `backend` 目录下运行：

```bash
pip install -r requirements.txt
```

## 3. 运行服务器

```bash
python main.py
```

服务器启动后，将在 `0.0.0.0:8080` 进行监听。

## 4. 数据库

系统会自动在当前目录创建 `crypto_lab.db` SQLite 数据库文件，你可以使用任何 SQLite 查看器（如 DB Browser for SQLite）来查看聊天记录和验证数据是否被加密存储。

## 5. 部署到云服务器

1. 将 `backend` 文件夹上传至云服务器。
2. 安装依赖并运行 `main.py`。
3. 确保云服务器防火墙已开放 `8080` 端口。
4. 修改前端代码中的连接地址，将 `ws://localhost:8080` 替换为 `ws://你的服务器IP:8080`。
