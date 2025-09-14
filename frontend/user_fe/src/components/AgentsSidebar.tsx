import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Bot, Play, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { AvailableAgent, AgentAnalysisResponse } from '@/services/api';

interface AgentsSidebarProps {
  agents: AvailableAgent[];
  activeAgentAnalyses: Record<string, AgentAnalysisResponse>;
  runningAgent: string | null;
  onRunAgent: (agentId: string) => void;
  className?: string;
}

const AgentsSidebar: React.FC<AgentsSidebarProps> = ({
  agents,
  activeAgentAnalyses,
  runningAgent,
  onRunAgent,
  className
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const getAgentStatus = (agentId: string) => {
    if (runningAgent === agentId) return 'running';
    if (activeAgentAnalyses[agentId]) {
      return activeAgentAnalyses[agentId].status === 'failed' ? 'error' : 'completed';
    }
    return 'idle';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Loader2 className="w-4 h-4 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Play className="w-4 h-4" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'running':
        return <Badge variant="default" className="bg-blue-100 text-blue-800">Running</Badge>;
      case 'completed':
        return <Badge variant="success">Completed</Badge>;
      case 'error':
        return <Badge variant="error">Failed</Badge>;
      default:
        return <Badge variant="outline">Ready</Badge>;
    }
  };

  return (
    <TooltipProvider>
      <div className={cn(
        "border-r bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm transition-all duration-300 h-full",
        isCollapsed ? "w-16" : "w-80",
        className
      )}>
        <div className="p-4 border-b flex items-center justify-between">
          {!isCollapsed && (
            <div className="flex items-center gap-2">
              <Bot className="w-6 h-6 text-primary" />
              <h2 className="text-lg font-semibold">AI Agents</h2>
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="h-8 w-8"
          >
            {isCollapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <ChevronLeft className="w-4 h-4" />
            )}
          </Button>
        </div>

        <div className="p-4 space-y-4">
          {!isCollapsed && (
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Select an agent to perform detailed analysis on your repository.
            </p>
          )}

          <div className="space-y-3">
            {agents.map((agent) => {
              const status = getAgentStatus(agent.agent_id);
              
              if (isCollapsed) {
                return (
                  <Tooltip key={agent.agent_id}>
                    <TooltipTrigger asChild>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => onRunAgent(agent.agent_id)}
                        disabled={!!runningAgent}
                        className="w-full h-12 relative"
                      >
                        {getStatusIcon(status)}
                        {status === 'completed' && (
                          <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full" />
                        )}
                        {status === 'error' && (
                          <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full" />
                        )}
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="right" className="max-w-xs">
                      <div>
                        <p className="font-medium">{agent.name}</p>
                        <p className="text-xs text-slate-500">{agent.description}</p>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                );
              }

              return (
                <Card key={agent.agent_id} className="overflow-hidden transition-all hover:shadow-md">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-base font-medium">{agent.name}</CardTitle>
                        <CardDescription className="text-sm mt-1">
                          {agent.description}
                        </CardDescription>
                      </div>
                      <div className="ml-2">
                        {getStatusBadge(status)}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <Button
                      onClick={() => onRunAgent(agent.agent_id)}
                      disabled={!!runningAgent}
                      className="w-full"
                      variant={status === 'completed' ? 'outline' : 'default'}
                    >
                      <div className="flex items-center gap-2">
                        {getStatusIcon(status)}
                        {status === 'running' ? 'Running...' : 
                         status === 'completed' ? 'Run Again' : 
                         status === 'error' ? 'Retry' : 'Run Analysis'}
                      </div>
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {!isCollapsed && agents.length > 0 && (
            <>
              <Separator />
              <div className="text-xs text-slate-500 dark:text-slate-400">
                {agents.filter(agent => getAgentStatus(agent.agent_id) === 'completed').length} of {agents.length} agents completed
              </div>
            </>
          )}
        </div>
      </div>
    </TooltipProvider>
  );
};

export default AgentsSidebar;