
import { SocketLog } from '../types';
import { getWsUrl } from '../config';

type Listener = (log: SocketLog) => void;

class RealSocketClient {
  private ws: WebSocket | null = null;
  private listeners: Listener[] = [];
  private messageHandlers: ((data: any) => void)[] = [];
  
  // 订阅日志用于 UI 显示
  subscribe(listener: Listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  // 注册收到消息的回调
  onMessage(handler: (data: any) => void) {
    this.messageHandlers.push(handler);
  }

  private emitLog(sender: 'CLIENT' | 'SERVER', message: string, type: 'INFO' | 'DATA' | 'Handshake' | 'Error' = 'INFO', details?: string) {
    this.listeners.forEach(l => l({
      id: Math.random().toString(36).substr(2, 9),
      timestamp: new Date().toLocaleTimeString(),
      sender,
      type,
      message,
      details
    }));
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const url = getWsUrl();
      this.emitLog('CLIENT', `尝试连接到服务器: ${url}...`, 'Handshake');
      
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        this.emitLog('CLIENT', 'WebSocket 连接成功建立', 'Handshake');
        resolve();
      };

      this.ws.onerror = (err) => {
        this.emitLog('CLIENT', '连接失败，请检查服务器是否启动', 'Error');
        reject(err);
      };

      this.ws.onclose = () => {
        this.emitLog('CLIENT', '连接已断开', 'Error');
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.messageHandlers.forEach(h => h(data));
        } catch (e) {
          console.error('Parse error', e);
        }
      };
    });
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      this.emitLog('CLIENT', '发送失败：未连接到服务器', 'Error');
    }
  }

  // 兼容旧代码的日志接口
  log(sender: 'CLIENT' | 'SERVER', message: string, type: 'INFO' | 'DATA' | 'Handshake' | 'Error' = 'INFO', details?: string) {
    this.emitLog(sender, message, type, details);
  }
}

export const socketSim = new RealSocketClient();
