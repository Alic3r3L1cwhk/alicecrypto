import React, { useState } from 'react';
import Layout from './components/Layout';
import PrivacyComputing from './components/PrivacyComputing';
import SecureChat from './components/SecureChat';
import { GoogleGenAI } from "@google/genai";

// Initialize Gemini (Though in this specific crypto simulation, we mostly use local logic, 
// we can use Gemini to generate a summary of the experiment if needed, but per the prompt instructions
// I will keep the Gemini initialization ready but focus on the specific crypto tasks requested).
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || '' });

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
