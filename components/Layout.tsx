import React from 'react';

interface LayoutProps {
  children: React.ReactNode;
  activeTab: 'compute' | 'chat';
  onTabChange: (tab: 'compute' | 'chat') => void;
}

const Layout: React.FC<LayoutProps> = ({ children, activeTab, onTabChange }) => {
  return (
    <div className="min-h-screen bg-cyber-900 text-cyber-text font-sans flex flex-col md:flex-row">
      {/* 侧边栏 */}
      <aside className="w-full md:w-64 bg-cyber-800 border-r border-cyber-700 flex-shrink-0">
        <div className="p-6 border-b border-cyber-700">
          <h1 className="text-lg font-bold text-cyber-accent tracking-tighter">
            AliceCrypto<span className="text-white">实验平台</span>
          </h1>
          <p className="text-xs text-cyber-dim mt-2">v1.0.0 [安全环境]</p>
        </div>
        
        <nav className="p-4 space-y-2">
          <button
            onClick={() => onTabChange('chat')}
            className={`w-full text-left px-4 py-3 rounded-md transition-all duration-200 flex items-center gap-3 ${
              activeTab === 'chat' 
                ? 'bg-cyber-500 text-cyber-accent border-l-4 border-cyber-accent' 
                : 'hover:bg-cyber-700 text-cyber-dim'
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <div>
              <div className="font-semibold">安全通信终端</div>
              <div className="text-[10px] opacity-70">中级实验：Socket/DH/AES</div>
            </div>
          </button>

          <button
            onClick={() => onTabChange('compute')}
            className={`w-full text-left px-4 py-3 rounded-md transition-all duration-200 flex items-center gap-3 ${
              activeTab === 'compute' 
                ? 'bg-cyber-500 text-cyber-accent border-l-4 border-cyber-accent' 
                : 'hover:bg-cyber-700 text-cyber-dim'
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            <div>
              <div className="font-semibold">隐私外包计算</div>
              <div className="text-[10px] opacity-70">高级实验：同态加密/Paillier</div>
            </div>
          </button>
        </nav>

        <div className="p-6 mt-auto">
          <div className="bg-cyber-700 rounded p-4 text-xs border border-cyber-500">
            <h3 className="text-cyber-accent font-bold mb-2">系统状态</h3>
            <div className="flex justify-between mb-1">
              <span>通信协议:</span>
              <span className="text-green-400">Encrypted (TLS 1.3)</span>
            </div>
            <div className="flex justify-between mb-1">
              <span>服务端:</span>
              <span className="text-blue-400">Python/Socket</span>
            </div>
             <div className="flex justify-between">
              <span>数据库:</span>
              <span className="text-yellow-400">就绪</span>
            </div>
          </div>
        </div>
      </aside>

      {/* 主内容区域 */}
      <main className="flex-1 overflow-auto bg-cyber-900 p-4 md:p-8">
        <header className="mb-8 flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-bold text-white">
              {activeTab === 'chat' ? '安全通信仿真终端' : '隐私保护外包计算系统'}
            </h2>
            <p className="text-cyber-dim mt-1">
              {activeTab === 'chat' 
                ? '基于 Socket 编程 / Diffie-Hellman 密钥交换 / AES-GCM 加密' 
                : '服务外包计算 / Paillier 同态加密 / 数据隐私保护'}
            </p>
          </div>
          <div className="hidden md:flex items-center space-x-2">
            <span className="h-3 w-3 bg-green-500 rounded-full animate-pulse"></span>
            <span className="text-xs font-mono text-green-500">网络连接正常</span>
          </div>
        </header>
        
        {children}
      </main>
    </div>
  );
};

export default Layout;