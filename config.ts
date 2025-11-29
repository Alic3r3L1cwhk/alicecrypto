
// === 服务器配置 ===

// !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
// 根据你的日志，我已经将这里预设为你刚才访问的 IP 地址
// 如果你的服务器 IP 变了，请手动修改这里
// !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
export const SERVER_HOST = 'localhost'; 

export const SERVER_PORT = 8080;

export const getWsUrl = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${SERVER_HOST}:${SERVER_PORT}`;
};
