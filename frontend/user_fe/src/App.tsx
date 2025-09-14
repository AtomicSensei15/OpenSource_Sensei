import React, { useState } from 'react';
import LandingPage from './pages/LandingPage';
import AnalysisPage from './pages/AnalysisPage';

type AppState = 'landing' | 'analysis';

function App() {
  const [currentPage, setCurrentPage] = useState<AppState>('landing');
  const [githubUrl, setGithubUrl] = useState('');

  const handleStartAnalysis = (url: string) => {
    setGithubUrl(url);
    setCurrentPage('analysis');
  };

  const handleBackToLanding = () => {
    setCurrentPage('landing');
    setGithubUrl('');
  };

  switch (currentPage) {
    case 'analysis':
      return (
        <AnalysisPage 
          githubUrl={githubUrl} 
          onBack={handleBackToLanding}
        />
      );
    default:
      return (
        <LandingPage 
          onAnalyze={handleStartAnalysis}
        />
      );
  }
}

export default App;
