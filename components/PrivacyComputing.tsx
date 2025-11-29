
import React, { useState, useEffect } from 'react';
import * as paillier from '../lib/paillier';
import { socketSim } from '../lib/socketSim';
import { EncryptedDataPacket } from '../types';

const PrivacyComputing: React.FC = () => {
  const [inputVal, setInputVal] = useState<string>('');
  const [dataPackets, setDataPackets] = useState<EncryptedDataPacket[]>([]);
  const [cloudResult, setCloudResult] = useState<string | null>(null);
  const [decryptedSum, setDecryptedSum] = useState<number | null>(null);
  const [processing, setProcessing] = useState(false);
  
  const pubKey = paillier.getPublicKey();

  useEffect(() => {
      // 监听计算结果
      socketSim.onMessage((data) => {
          if (data.type === 'COMPUTE_RESULT') {
              setProcessing(false);
              setCloudResult(data.result);
              socketSim.log('SERVER', '收到云端计算结果', 'DATA', data.result.substring(0, 20) + '...');
          }
      });
  }, []);

  const handleEncryptAndStore = () => {
    const num = parseInt(inputVal);
    if (isNaN(num)) return;

    // 前端模拟同态加密 (实际场景下，为了配合后端 phe 库，我们需要确保这里的 paillier 实现和后端兼容)
    // 注意：当前 lib/paillier.ts 使用的是小素数演示，而 Python 后端通常使用大素数。
    // 在这个混合演示中，我们将使用前端生成的密文发给后端。
    // *重要*：为了保证实验成功，这里我们依然使用 lib/paillier.ts 进行加密。
    // 如果想要后端能解密或操作，后端必须知道 n 和 n^2。
    // 在本实验协议中，我们将把 n 和 g 传给后端。
    
    const ciphertext = paillier.encrypt(num);
    socketSim.log('CLIENT', `加密数值: ${num}`, 'INFO');
    
    const packet: EncryptedDataPacket = {
      id: Math.random().toString(36).substr(2, 5),
      originalValue: num,
      ciphertext: ciphertext
    };

    setDataPackets(prev => [...prev, packet]);
    setInputVal('');
  };

  const handleOutsourceCalculation = async () => {
    if (dataPackets.length === 0) return;
    setProcessing(true);
    setCloudResult(null);
    setDecryptedSum(null);

    // 确保连接
    await socketSim.connect().catch(() => {});

    socketSim.log('CLIENT', `发送 ${dataPackets.length} 条密文到云端求和`, 'DATA');
    
    // 发送符合 server.py 协议的数据
    socketSim.send({
        type: 'COMPUTE_SUM',
        pub_key: {
            n: pubKey.n,
            g: pubKey.g
        },
        values: dataPackets.map(p => p.ciphertext)
    });
  };

  const handleDecryptResult = () => {
    if (!cloudResult) return;
    try {
        const result = paillier.decrypt(cloudResult);
        setDecryptedSum(result);
        socketSim.log('CLIENT', `解密成功。总和为 ${result}。`, 'INFO');
    } catch(e) {
        socketSim.log('CLIENT', `解密失败`, 'Error');
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-cyber-800 rounded-lg p-6 border border-cyber-700 shadow-lg">
          <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <span className="text-cyber-accent">01.</span> 数据输入
          </h3>
          <div className="flex gap-2 mb-6">
            <input
              type="number"
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              placeholder="输入数值"
              className="flex-1 bg-cyber-900 border border-cyber-600 rounded px-4 py-2 focus:outline-none focus:border-cyber-accent text-white"
            />
            <button onClick={handleEncryptAndStore} className="bg-cyber-500 hover:bg-cyber-400 text-white px-4 py-2 rounded font-semibold transition-colors border border-cyber-500">
              加密并添加
            </button>
          </div>
          <div className="bg-cyber-900 rounded p-4 h-48 overflow-y-auto border border-cyber-700">
             {dataPackets.map((pkt) => (
                 <div key={pkt.id} className="grid grid-cols-3 gap-2 text-xs font-mono border-b border-cyber-800 py-2 hover:bg-cyber-800">
                     <span className="text-gray-400">{pkt.id}</span>
                     <span className="text-green-400">{pkt.originalValue}</span>
                     <span className="text-gray-500 truncate">{pkt.ciphertext.substring(0, 15)}...</span>
                 </div>
             ))}
          </div>
        </div>

        <div className="bg-cyber-800 rounded-lg p-6 border border-cyber-700 shadow-lg flex flex-col justify-center">
            <h3 className="text-xl font-bold text-white mb-4 text-center">同态加密参数</h3>
            <div className="space-y-4 text-center">
                <div className="p-2 bg-cyber-900 rounded">
                    <div className="text-cyber-dim text-xs">模数 N</div>
                    <div className="text-cyber-accent font-mono truncate">{pubKey.n}</div>
                </div>
                <div className="p-2 bg-cyber-900 rounded">
                    <div className="text-cyber-dim text-xs">生成元 G</div>
                    <div className="text-cyber-accent font-mono truncate">{pubKey.g}</div>
                </div>
            </div>
        </div>
      </div>

      <div className="flex justify-center my-4">
          <button
            onClick={handleOutsourceCalculation}
            disabled={processing || dataPackets.length === 0}
            className={`px-8 py-4 rounded-full font-bold text-lg shadow-lg transition-all transform hover:scale-105 ${
                processing ? 'bg-cyber-700 text-gray-400' : 'bg-cyber-accent text-cyber-900 hover:bg-white'
            }`}
          >
              {processing ? "云端计算中..." : "发起安全云端外包计算"}
          </button>
      </div>

      {cloudResult && (
        <div className="bg-gradient-to-r from-cyber-800 to-cyber-900 rounded-lg p-6 border border-cyber-500 shadow-lg text-center">
             <h3 className="text-xl font-bold text-white mb-4">收到云端结果</h3>
             <div className="bg-black/50 p-3 rounded font-mono text-xs break-all border border-cyber-700 mb-4 text-yellow-500">
                 {cloudResult}
             </div>
             {decryptedSum === null ? (
                <button onClick={handleDecryptResult} className="px-6 py-2 border-2 border-cyber-accent text-cyber-accent rounded hover:bg-cyber-accent hover:text-cyber-900 transition-colors uppercase font-bold">
                    使用私钥解密
                </button>
             ) : (
                 <div className="text-4xl font-mono font-bold text-green-400 animate-pulse">
                     {decryptedSum}
                 </div>
             )}
        </div>
      )}
    </div>
  );
};

export default PrivacyComputing;
