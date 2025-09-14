import React, { useState, useEffect, useCallback } from 'react';
import { CheckCircle, AlertCircle, Loader2, ArrowLeft, ExternalLink, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
  
  const renderJson = (json: object) => {
    return (
      <pre className="bg-slate-100 dark:bg-slate-800 p-4 rounded-md text-sm overflow-auto max-h-96">
        {JSON.stringify(json, null, 2)}
      </pre>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center p-4">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-primary animate-spin mx-auto mb-4" />
          <h2 className="text-xl font-semibold">Performing Initial Analysis...</h2>
          <p className="text-slate-600 dark:text-slate-300">Cloning repository and running initial checks. This may take a moment.</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><AlertCircle className="text-red-500" /> Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-slate-600 dark:text-slate-300 mb-4">{error}</p>
            <Button onClick={onBack} variant="outline" className="w-full">
              <ArrowLeft className="w-4 h-4 mr-2" /> Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }
  
  const AGENT_MAP = initialAnalysis?.available_agents.reduce((acc: Record<string, AvailableAgent>, agent: AvailableAgent) => {
    acc[agent.agent_id] = agent;
    return acc;
  }, {} as Record<string, AvailableAgent>) || {};


  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <header className="border-b bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button onClick={onBack} variant="ghost" size="icon"><ArrowLeft className="w-5 h-5" /></Button>
            <div>
              <h1 className="text-xl font-semibold">{initialAnalysis?.repo_url.split('/').slice(-2).join('/')}</h1>
              <a href={initialAnalysis?.repo_url} target="_blank" rel="noopener noreferrer" className="text-sm text-slate-500 hover:text-primary flex items-center gap-1">
                View on GitHub <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto p-4 md:p-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1 space-y-6">
          <h2 className="text-2xl font-bold">Analysis Agents</h2>
          <p className="text-slate-600 dark:text-slate-400">
            {initialAnalysis?.message} Click on an agent to perform a detailed analysis.
          </p>
          <div className="space-y-4">
            {initialAnalysis?.available_agents.map((agent: AvailableAgent) => (
              <Card key={agent.agent_id} className="overflow-hidden">
                <CardHeader>
                  <CardTitle className="text-lg">{agent.name}</CardTitle>
                  <CardDescription>{agent.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button
                    onClick={() => handleRunAgent(agent.agent_id)}
                    disabled={!!runningAgent}
                    className="w-full"
                  >
                    {runningAgent === agent.agent_id ? (
                      <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Running...</>
                    ) : activeAgentAnalyses[agent.agent_id] ? (
                      <><CheckCircle className="w-4 h-4 mr-2" /> Run Again</>
                    ) : (
                      <><Sparkles className="w-4 h-4 mr-2" /> Run Analysis</>
                    )}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        <div className="lg:col-span-2 space-y-6">
           <h2 className="text-2xl font-bold">Analysis Results</h2>
           <Card>
              <CardHeader>
                  <CardTitle>Initial Repository Overview</CardTitle>
                  <CardDescription>
                    A high-level summary from the Repository Analyzer Agent.
                  </CardDescription>
              </CardHeader>
              <CardContent>
                  {initialAnalysis?.initial_summary ? renderJson(initialAnalysis.initial_summary) : <p>No summary available.</p>}
              </CardContent>
           </Card>
           
           {Object.values(activeAgentAnalyses).map(analysis => (
            <Card key={analysis.agent_id}>
              <CardHeader>
                <CardTitle className="flex justify-between items-center">
                  <span>{AGENT_MAP[analysis.agent_id]?.name || 'Agent'} Results</span>
                  {analysis.status === 'failed' ? <AlertCircle className="text-red-500"/> : <CheckCircle className="text-green-500" />}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {renderJson(analysis.result)}
              </CardContent>
            </Card>
           ))}
        </div>
      </main>
    </div>
  );
};

export default AnalysisPage;

