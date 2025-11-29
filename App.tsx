import React, { useState } from 'react';
import Layout from './components/Layout';
import PrivacyComputing from './components/PrivacyComputing';
import SecureChat from './components/SecureChat';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'compute' | 'chat'>('compute');

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      {activeTab === 'compute' ? (
        <PrivacyComputing />
      ) : (
        <SecureChat />
      )}
    </Layout>
  );
};

export default App;