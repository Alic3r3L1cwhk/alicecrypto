
// === 服务器配置 ===

// !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
// 重要: 请将下面的 'localhost' 修改为你的云服务器公网 IP 地址
// 例如: export const SERVER_HOST = '47.110.123.45';
// !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
export const SERVER_HOST = 'localhost'; 

export const SERVER_PORT = 8080;

export const getWsUrl = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${SERVER_HOST}:${SERVER_PORT}`;
};
