import React, { useState, useEffect, useCallback } from 'react';
import { AlertCircle, Loader2, ArrowLeft } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import MainLayout from '@/components/MainLayout';
import AgentsSidebar from '@/components/AgentsSidebar';
import AgentResultVisualization from '@/components/AgentResultVisualization';
// import { Separator } from '@/components/ui/separator';
import apiService from '@/services/api';
import type { InitialAnalysisResponse, AgentAnalysisResponse, AvailableAgent } from '@/services/api';

interface AnalysisPageProps {
  githubUrl: string;
  onBack: () => void;
}

const AnalysisPage: React.FC<AnalysisPageProps> = ({ githubUrl, onBack }) => {
  const [initialAnalysis, setInitialAnalysis] = useState<InitialAnalysisResponse | null>(null);
  const [activeAgentAnalyses, setActiveAgentAnalyses] = useState<Record<string, AgentAnalysisResponse>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [runningAgent, setRunningAgent] = useState<string | null>(null);

  const performInitialAnalysis = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.startAnalysis({ repo_url: githubUrl });
      setInitialAnalysis(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start analysis');
    } finally {
      setLoading(false);
    }
  }, [githubUrl]);

  useEffect(() => {
    performInitialAnalysis();
  }, [performInitialAnalysis]);

  const handleRunAgent = async (agentId: string) => {
    if (!initialAnalysis || runningAgent) return;
    setRunningAgent(agentId);
    try {
      const result = await apiService.runAgentAnalysis(initialAnalysis.analysis_id, agentId);
      setActiveAgentAnalyses(prev => ({ ...prev, [agentId]: result }));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Agent analysis failed';
      setActiveAgentAnalyses(prev => ({
        ...prev,
        [agentId]: {
          analysis_id: initialAnalysis.analysis_id,
          agent_id: agentId,
          status: 'failed',
          result: { error: errorMessage },
        },
      }));
    } finally {
      setRunningAgent(null);
    }
  };
  
  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-full p-8">
          <div className="text-center">
            <Loader2 className="w-12 h-12 text-primary animate-spin mx-auto mb-4" />
            <h2 className="text-xl font-semibold">Performing Initial Analysis...</h2>
            <p className="text-slate-600 dark:text-slate-300">Cloning repository and running initial checks. This may take a moment.</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  if (error) {
    return (
      <MainLayout onBack={onBack}>
        <div className="flex items-center justify-center h-full p-8">
          <Card className="max-w-md w-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertCircle className="text-red-500" /> 
                Error
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600 dark:text-slate-300 mb-4">{error}</p>
              <Button onClick={onBack} variant="outline" className="w-full">
                <ArrowLeft className="w-4 h-4 mr-2" /> Go Back
              </Button>
            </CardContent>
          </Card>
        </div>
      </MainLayout>
    );
  }
  
  const AGENT_MAP = initialAnalysis?.available_agents.reduce((acc: Record<string, AvailableAgent>, agent: AvailableAgent) => {
    acc[agent.agent_id] = agent;
    return acc;
  }, {} as Record<string, AvailableAgent>) || {};

  const sidebar = (
    <AgentsSidebar
      agents={initialAnalysis?.available_agents || []}
      activeAgentAnalyses={activeAgentAnalyses}
      runningAgent={runningAgent}
      onRunAgent={handleRunAgent}
    />
  );

  return (
    <MainLayout
      sidebar={sidebar}
      title={initialAnalysis?.repo_url.split('/').slice(-2).join('/')}
      subtitle="View on GitHub"
      externalLink={initialAnalysis?.repo_url}
      onBack={onBack}
    >
      <div className="p-6 space-y-6">
        {/* Initial Summary */}
        {initialAnalysis?.initial_summary && (
          <Card>
            <CardHeader>
              <CardTitle>Initial Repository Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <AgentResultVisualization
                agentId="repository_analyzer"
                agentName="Repository Analyzer"
                result={initialAnalysis.initial_summary}
                status="completed"
              />
            </CardContent>
          </Card>
        )}

        {/* Agent Results */}
        {Object.values(activeAgentAnalyses).map(analysis => (
          <AgentResultVisualization
            key={analysis.agent_id}
            agentId={analysis.agent_id}
            agentName={AGENT_MAP[analysis.agent_id]?.name || 'Agent'}
            result={analysis.result}
            status={analysis.status}
          />
        ))}

        {/* Placeholder when no results */}
        {Object.keys(activeAgentAnalyses).length === 0 && (
          <div className="text-center py-12">
            <div className="text-slate-400 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-slate-600 dark:text-slate-300 mb-2">
              Ready for Analysis
            </h3>
            <p className="text-slate-500 dark:text-slate-400">
              Select an agent from the sidebar to start analyzing your repository.
            </p>
          </div>
        )}
      </div>
    </MainLayout>
  );
};

export default AnalysisPage;

