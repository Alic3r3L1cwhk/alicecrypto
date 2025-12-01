import React, { useState } from 'react';
import Layout from './components/Layout';
import FHE from './components/FHE';
import SecureChat from './components/SecureChat';
import MPC from './components/MPC';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'fhe' | 'mpc' | 'chat'>('fhe');

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      {activeTab === 'fhe' && <FHE />}
      {activeTab === 'mpc' && <MPC />}
      {activeTab === 'chat' && <SecureChat />}
    </Layout>
  );
};

export default App;