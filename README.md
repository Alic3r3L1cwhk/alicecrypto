# AliceCrypto v2.2 全面隐私计算实验台

AliceCrypto v2.2 重新整理了前后端架构，移除了早期的 SecureChat 模拟通道，转而集中展示 **FHE（多算法全同态加密）** 与 **MPC（百万富翁协议 & Shamir 门限方案）** 的端到端链路。所有敏感操作均通过统一的 WebSocket 服务完成，并附带系统时钟与密钥轮换广播，便于课堂或演示场景实时追踪。

---

## 🔑 核心能力

- **多算法 FHE 引擎**：Paillier、RSA、ElGamal 三种算法同时在线，由 `backend/fhe_service.py` 统一调度，支持批量加密与云端 SUM/PRODUCT 计算。
- **5 分钟密钥轮换**：后台线程固定间隔刷新密钥对并广播 `KEY_ROTATED` 事件，同时返回服务器时钟，前端以倒计时方式可视化轮换周期。
- **MPC 控制台**：Shamir 秘密拆分/重构本地演示 + 通过 WebSocket 启动百万富翁协议，结果与传输层日志实时同步。
- **统一状态面板**：前端 FHE、MPC 页面均能订阅 `SERVER_TIME` 与最新公钥信息，展示 bit-length、Operation、下一次轮换时间等指标。

---

## 🧱 架构速览

```
┌──────────────┐     WebSocket (JSON 消息)     ┌────────────────────┐
│ React + Vite │  <-------------------------->  │ Python asyncio svc │
│ components/* │                                │ backend/main.py    │
└──────────────┘                                └────────────────────┘
     ▲   ▲                                               │
     │   └── socketSim.ts 统一管理连接与日志             │
     └──── FHE.tsx / MPC.tsx 共享服务时钟和密钥状态  ───┘
```

- 监听端口：`ws://<host>:8080`
- 主要模块：`backend/main.py`（WebSocket 路由）、`backend/fhe_service.py`（FHE 引擎）、`components/FHE.tsx`、`components/MPC.tsx`

---

## 🛰️ WebSocket 消息速查

| 类型                  | 方向        | 说明                                                                    |
| --------------------- | ----------- | ----------------------------------------------------------------------- |
| `GET_FHE_KEY`         | 前端 → 后端 | 请求指定算法的公钥与 `key_info`（包含倒计时）。                         |
| `BATCH_ENCRYPT`       | 前端 → 后端 | 发送 `{algorithm, values[]}`，返回 `ENCRYPTED_BATCH`。                  |
| `COMPUTE_FHE`         | 前端 → 后端 | 发送同态密文数组，收到 `COMPUTE_RESULT`（含 `operation` 与可选明文）。  |
| `SERVER_TIME`         | 后端 → 前端 | `GET_SERVER_TIME` 或轮换广播触发，提供 `timestamp` 与 `keys` 全量信息。 |
| `KEY_ROTATED`         | 后端 → 前端 | 每 5 分钟推送一次，提醒 UI 更新公钥、倒计时。                           |
| `MPC_GENERATE_SECRET` | 前端 → 后端 | 请求服务器生成 Bob 的秘密数值。                                         |
| `MPC_COMPARE_INIT`    | 前端 → 后端 | 发送 Alice 金额，返回 `MPC_COMPARE_RESULT`。                            |

SecureChat/ECDH/AES 相关消息已全部移除；若历史版本仍有 `CHAT_MESSAGE` 请求，请升级前端或停止调用。

---

## ⚙️ 部署步骤

### 1. 后端服务

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate  # Windows 示例，可自行选择环境
pip install -r requirements.txt
python main.py  # 默认监听 0.0.0.0:8080，并输出 backend.log
```

### 2. 前端（Vite）

```bash
npm install
npm run dev     # 开发模式
# 或
npm run build && npm run preview
```

默认前端运行在 `http://localhost:5173/`（dev）或 `http://localhost:4173/`（preview）。如需对外访问，可通过 nginx 或 `npm run preview -- --host` 暴露。

---

## 📌 运维提醒

- 确认浏览器允许访问 `ws://<host>:8080`，否则 FHE/MPC 页面将保持离线状态并在日志面板提示。
- 如果需要调整密钥轮换周期，可修改 `FHEManager(rotation_interval=...)`，但前端仍会根据 `key_info.rotation_interval` 自动适配倒计时。
- 旧版数据库 (`backend/database.py`) 和 SecureChat 工具仅作为历史兼容占位，不再被 `main.py` 引用。

> 建议通过 Git 标签保留 v2.0 之前的 SecureChat 演示，如需对比教学，可在文档中指向该标签。当前主分支聚焦“多算法 FHE + MPC” 核心能力。