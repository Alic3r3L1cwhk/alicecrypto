
// === 服务器配置 ===
// 请将此处修改为你云服务器的公网 IP 地址
// 如果是在本地测试，请保持 localhost
export const SERVER_CONFIG = {
  HOST: 'localhost', // 部署时修改为你的云服务器 IP，例如 '1.2.3.4'
  PORT: 8080
};

export const getWsUrl = () => `ws://${SERVER_CONFIG.HOST}:${SERVER_CONFIG.PORT}`;
