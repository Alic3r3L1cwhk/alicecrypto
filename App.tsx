
import React, { useState } from 'react';
import Layout from './components/Layout';
import FHE from './components/FHE';
import MPC from './components/MPC';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'fhe' | 'mpc'>('mpc');

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      {activeTab === 'fhe' && <FHE />}
      {activeTab === 'mpc' && <MPC />}
    </Layout>
  );
};

export default App;
