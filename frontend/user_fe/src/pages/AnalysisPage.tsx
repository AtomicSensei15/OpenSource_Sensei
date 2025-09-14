import React, { useState, useEffect, useCallback } from 'react';
import { Bot, GitBranch, Clock, CheckCircle, AlertCircle, Loader2, ArrowLeft, ExternalLink } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { apiService } from '../services/api';
import type { Project, Analysis, Agent } from '../services/api';

interface AnalysisPageProps {
  githubUrl: string;
  onBack: () => void;
}

const AnalysisPage: React.FC<AnalysisPageProps> = ({ githubUrl, onBack }) => {
  const [project, setProject] = useState<Project | null>(null);
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const initializeAnalysis = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Parse GitHub URL
      const urlMatch = githubUrl.match(/github.com\/([^/]+)\/([^/]+)/);
      if (!urlMatch) {
        throw new Error('Invalid GitHub URL format');
      }

      const [, owner, repo] = urlMatch;
      const repoName = repo.replace(/\.git$/, '');

      // Create project
      const newProject = await apiService.createProject({
        name: `${owner}/${repoName}`,
        description: `Analysis of ${owner}/${repoName} repository`,
        project_type: 'github_repo',
        source_url: githubUrl,
        branch: 'main'
      });

      setProject(newProject);

      // Get available agents
      const agentsResponse = await apiService.getAgents();
      setAgents(agentsResponse.data);

      // Create analyses for each agent type
      const analysisTypes = [
        { type: 'code_review', name: 'Code Quality Review', agent_type: 'code_review_agent' },
        { type: 'research', name: 'Technology Research', agent_type: 'research_agent' },
        { type: 'qa_review', name: 'QA Assessment', agent_type: 'qa_agent' },
        { type: 'architecture', name: 'Architecture Analysis', agent_type: 'repository_analyzer' }
      ];

      const createdAnalyses = await Promise.all(
        analysisTypes.map(analysisType =>
          apiService.createAnalysis({
            name: analysisType.name,
            description: `${analysisType.name} for ${owner}/${repoName}`,
            analysis_type: analysisType.type,
            config: {
              project_id: newProject.id,
              repository_url: githubUrl,
              agent_type: analysisType.agent_type
            }
          })
        )
      );

      setAnalyses(createdAnalyses);
      
      // Start polling for updates
      startPolling(newProject.id);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start analysis');
    } finally {
      setLoading(false);
    }
  }, [githubUrl]);

  useEffect(() => {
    initializeAnalysis();
  }, [initializeAnalysis]);

  const startPolling = (projectId: string) => {
    const interval = setInterval(async () => {
      try {
        // Update project status
        const updatedProject = await apiService.getProject(projectId);
        setProject(updatedProject);

        // Update analyses
        const analysesResponse = await apiService.getAnalyses({ project_id: projectId });
        setAnalyses(analysesResponse.data);

        // Stop polling if all analyses are complete
        const allComplete = analysesResponse.data.every(
          analysis => ['completed', 'failed', 'cancelled'].includes(analysis.status)
        );
        
        if (allComplete || updatedProject.status === 'completed') {
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 2000);

    // Clean up after 10 minutes
    setTimeout(() => clearInterval(interval), 600000);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'running':
      case 'analyzing':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return <Clock className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'failed':
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'running':
      case 'analyzing':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      default:
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-primary animate-spin mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Initializing Analysis</h2>
          <p className="text-slate-600 dark:text-slate-300">Setting up AI agents for your repository...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center">
        <Card className="max-w-md w-full mx-4">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-6 h-6 text-red-500" />
              <CardTitle>Analysis Failed</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-slate-600 dark:text-slate-300 mb-4">{error}</p>
            <div className="flex space-x-2">
              <Button onClick={onBack} variant="outline" className="flex-1">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <Button onClick={initializeAnalysis} className="flex-1">
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const overallProgress = project && analyses.length > 0 
    ? analyses.reduce((sum, analysis) => sum + analysis.progress_percentage, 0) / analyses.length
    : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="border-b bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button onClick={onBack} variant="ghost" size="sm">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <div>
                <h1 className="text-xl font-semibold">{project?.name}</h1>
                <div className="flex items-center space-x-2 text-sm text-slate-500">
                  <GitBranch className="w-4 h-4" />
                  <span>{project?.branch || 'main'}</span>
                  <a 
                    href={project?.source_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex items-center space-x-1 hover:text-slate-700"
                  >
                    <ExternalLink className="w-3 h-3" />
                    <span>View on GitHub</span>
                  </a>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className={`px-3 py-1 rounded-full text-sm border ${getStatusColor(project?.status || 'created')}`}>
                {getStatusIcon(project?.status || 'created')}
                <span className="ml-2 capitalize">{project?.status || 'created'}</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Overall Progress */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Bot className="w-5 h-5" />
              <span>Analysis Progress</span>
            </CardTitle>
            <CardDescription>
              Our AI agents are analyzing your repository
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>Overall Progress</span>
                  <span>{Math.round(overallProgress)}%</span>
                </div>
                <Progress value={overallProgress} className="h-2" />
              </div>
              
              {project && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-slate-500">Files:</span>
                    <div className="font-semibold">{project.total_files}</div>
                  </div>
                  <div>
                    <span className="text-slate-500">Lines:</span>
                    <div className="font-semibold">{project.total_lines.toLocaleString()}</div>
                  </div>
                  <div>
                    <span className="text-slate-500">Started:</span>
                    <div className="font-semibold">
                      {project.started_at ? new Date(project.started_at).toLocaleTimeString() : 'Not started'}
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-500">Phase:</span>
                    <div className="font-semibold">{project.current_phase || 'Initializing'}</div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Agent Analysis Results */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="code-review">Code Review</TabsTrigger>
            <TabsTrigger value="research">Research</TabsTrigger>
            <TabsTrigger value="qa-review">QA Review</TabsTrigger>
            <TabsTrigger value="architecture">Architecture</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {analyses.map((analysis) => (
                <Card key={analysis.id}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">{analysis.name}</CardTitle>
                      {getStatusIcon(analysis.status)}
                    </div>
                    <CardDescription>{analysis.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Progress</span>
                          <span>{analysis.progress_percentage}%</span>
                        </div>
                        <Progress value={analysis.progress_percentage} className="h-1" />
                      </div>
                      
                      {analysis.current_step && (
                        <div className="text-sm text-slate-600 dark:text-slate-300">
                          Current: {analysis.current_step}
                        </div>
                      )}
                      
                      {analysis.status === 'completed' && analysis.summary && (
                        <div className="mt-3 p-3 bg-slate-50 dark:bg-slate-800 rounded text-sm">
                          {analysis.summary}
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
              {agents.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Active Agents</CardTitle>
                    <CardDescription>Statuses of participating agents</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2 text-sm">
                      {agents.map(a => (
                        <li key={a.id} className="flex items-center justify-between border-b last:border-b-0 pb-1">
                          <span>{a.name}</span>
                          <span className="capitalize text-slate-500">{a.status}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          {/* Individual agent result tabs would be populated with detailed results */}
          {['code-review', 'research', 'qa-review', 'architecture'].map((tabValue) => (
            <TabsContent key={tabValue} value={tabValue}>
              <Card>
                <CardHeader>
                  <CardTitle>
                    {analyses.find(a => a.analysis_type === tabValue.replace('-', '_'))?.name || 'Analysis'}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {(() => {
                    const analysis = analyses.find(a => a.analysis_type === tabValue.replace('-', '_'));
                    if (!analysis) {
                      return <p>Analysis not found</p>;
                    }
                    
                    if (analysis.status === 'completed' && analysis.results) {
                      return (
                        <div className="space-y-4">
                          <pre className="bg-slate-50 dark:bg-slate-800 p-4 rounded text-sm overflow-auto">
                            {JSON.stringify(analysis.results, null, 2)}
                          </pre>
                          {analysis.recommendations && analysis.recommendations.length > 0 && (
                            <div>
                              <h4 className="font-semibold mb-2">Recommendations:</h4>
                              <ul className="space-y-2">
                                {analysis.recommendations.map((rec, index) => (
                                  <li key={index} className="flex items-start space-x-2">
                                    <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                                    <span className="text-sm">{JSON.stringify(rec)}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      );
                    } else if (analysis.status === 'failed') {
                      return (
                        <div className="text-center py-8">
                          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                          <h3 className="font-semibold mb-2">Analysis Failed</h3>
                          <p className="text-slate-600 dark:text-slate-300">
                            {analysis.error_message || 'An error occurred during analysis'}
                          </p>
                        </div>
                      );
                    } else {
                      return (
                        <div className="text-center py-8">
                          <Loader2 className="w-12 h-12 text-primary animate-spin mx-auto mb-4" />
                          <h3 className="font-semibold mb-2">Analysis in Progress</h3>
                          <p className="text-slate-600 dark:text-slate-300">
                            {analysis.current_step || 'Processing your repository...'}
                          </p>
                        </div>
                      );
                    }
                  })()}
                </CardContent>
              </Card>
            </TabsContent>
          ))}
        </Tabs>
      </div>
    </div>
  );
};

export default AnalysisPage;