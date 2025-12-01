# AliceCrypto v2.0 安全多方计算平台

**AliceCrypto v2.0** 是一个用于展示前沿密码学技术的综合实验平台。新版本强化了前端三大控制台（Secure Chat、FHE、MPC），并同步升级后端 WebSocket 服务，确保所有演示都基于真实的密码学协议完成端到端联动。

---

## 🚀 v2.0 特性总览

1. **MPC 安全多方计算控制台**：支持 Shamir 门限分片交互演示，以及后端驱动的 Millionaires Problem（`MPC_GENERATE_SECRET` / `MPC_COMPARE_INIT`）。
2. **FHE 全同态加密引擎**：提供 Paillier 云端求和、密钥轮换提醒（`KEY_ROTATED`）和服务端直连密钥模式，界面模拟 CKKS/BFV 参数面板。
3. **Secure Chat**：基于 ECDH + AES-GCM 的安全信道，支持浏览器 WebCrypto 与软件 Polyfill 双栈自动回退。
4. **实时日志与数据可视化**：前端集中展示 WebSocket 流量、密文、解密结果与 MPC 协议输出，便于课堂演示或实验汇报。

---

## 🔌 后端服务能力

- **统一 WebSocket 网关**：监听 `ws://<SERVER_HOST>:8080`，负责握手、聊天、FHE 与 MPC 全部消息类型。
- **安全信道**：为每个连接动态生成 ECDH 密钥对，并通过 AES-GCM 对聊天流量进行加解密，同时把密文落库 (`crypto_lab.db`) 便于审计。
- **Paillier 轮换广播**：后端每 5 分钟自动刷新 2048-bit 密钥，并向所有在线客户端推送 `KEY_ROTATED`（包含新公钥与时间窗口），同步前端状态指示灯。
- **MPC 会话管理**：为每个客户端维护独立的 Bob 密密数，`MPC_SECRET_GENERATED` 事件返回成功标记，`MPC_COMPARE_RESULT` 则输出 Alice/Bob 的相对大小。
- **容错日志**：所有请求都会写入 `backend.log`，便于在服务器上排查连接/协议问题。

---

## ⚙️ 配置与运行

### 1. 后端（Python + WebSockets）

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py
```

- 默认监听 `0.0.0.0:8080`，可通过反向代理或防火墙规则向公网暴露。
- 运行后会生成 `backend.log` 与 `crypto_lab.db`，确保目录具备写权限。
- 若需调整密钥轮换周期，可修改 `paillier_service.KEY_ROTATION_INTERVAL`。

### 2. 前端（Vite + React）

```bash
npm install
npm run dev      # 本地调试
npm run build    # 生产构建
npm run preview  # 部署前预览
```

- 若将后端部署在远程服务器，请更新 `config.ts` 中的 `SERVER_HOST` / `SERVER_PORT`，让 WebSocket 指向正确地址。

### 3. 快速验证

1. 启动后端后，打开前端页面，点击 Secure Chat 的「连接服务器」，日志面板应显示 `HANDSHAKE` 与 `AES-GCM` 建链成功。
2. 在 FHE 标签页请求公钥、加密整数并发送「云端执行」，应收到 `COMPUTE_RESULT_SERVER_KEY`，同时在服务器控制台看到日志。
3. 在 MPC 标签页生成 Bob 的秘密，再输入不同的 Alice 值触发安全比对，前端会展示 `Alice is Richer / Bob is Richer` 等结果。

---

## 📦 部署到云端

1. **后端**：通过 `systemd`、`supervisor` 或 `pm2`（配合 `python main.py`）保持 WebSocket 服务常驻，并开放 `8080` 端口。
2. **前端**：`npm run build` 后将 `dist/` 部署到任何静态服务器（Nginx、Vercel、静态 OSS 等），或直接 `npm run preview` 暴露在 `3000` 端口。
3. **反向代理**：若需要 HTTPS，可在 Nginx 中配置 `wss://` 转发到本机 `8080`，并让前端通过相同域名访问。

完成以上配置后即可在浏览器端体验端到端的安全多方计算演示。祝实验顺利！