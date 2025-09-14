import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { AlertCircle, CheckCircle, FileText, GitBranch, Star, Users, Code } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, PieChart, Pie, Cell } from 'recharts';
import { MetricCard, IssueList, ChartContainer, COLORS } from '@/components/AnalyticsComponents';
import type { JsonObject } from '@/services/api';

interface AgentResultVisualizationProps {
  agentId: string;
  agentName: string;
  result: JsonObject;
  status: string;
}

const AgentResultVisualization: React.FC<AgentResultVisualizationProps> = ({
  agentId,
  agentName,
  result,
  status
}) => {
  const renderRepositoryAnalysis = (data: JsonObject) => {
    const stats = data.repository_stats as JsonObject;
    const languages = data.languages as JsonObject;
    const fileTypes = data.file_types as JsonObject;

    return (
      <div className="space-y-6">
        {/* Repository Stats */}
        {stats && (
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <GitBranch className="w-5 h-5" />
              Repository Statistics
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard
                title="Total Files"
                value={stats.total_files as number}
                icon={<FileText className="w-5 h-5" />}
                color="bg-blue-500"
              />
              <MetricCard
                title="Lines of Code"
                value={(stats.total_lines as number).toLocaleString()}
                icon={<Code className="w-5 h-5" />}
                color="bg-green-500"
              />
              <MetricCard
                title="Commits"
                value={stats.total_commits as number}
                icon={<GitBranch className="w-5 h-5" />}
                color="bg-purple-500"
              />
              <MetricCard
                title="Contributors"
                value={stats.contributors as number}
                icon={<Users className="w-5 h-5" />}
                color="bg-yellow-500"
              />
            </div>
          </div>
        )}

        {/* Languages Chart */}
        {languages && Object.keys(languages).length > 0 && (
          <ChartContainer title="Language Distribution" height={300}>
            <PieChart>
              <Pie
                data={Object.entries(languages).map(([lang, percentage]) => ({
                  name: lang,
                  value: percentage as number
                }))}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name} ${value}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {Object.entries(languages).map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ChartContainer>
        )}

        {/* File Types */}
        {fileTypes && Object.keys(fileTypes).length > 0 && (
          <ChartContainer title="File Types Distribution" height={300}>
            <BarChart data={Object.entries(fileTypes).map(([type, count]) => ({
              type,
              count: count as number
            }))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="type" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill={COLORS[0]} />
            </BarChart>
          </ChartContainer>
        )}
      </div>
    );
  };

  const renderCodeReviewResults = (data: JsonObject) => {
    const issues = data.issues as JsonObject[];
    const metrics = data.code_quality_metrics as JsonObject;
    const suggestions = data.improvement_suggestions as JsonObject[];

    return (
      <div className="space-y-6">
        {/* Code Quality Metrics */}
        {metrics && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Star className="w-5 h-5" />
                Code Quality Score
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-2">
                    <span>Overall Quality</span>
                    <span className="font-bold">{metrics.overall_score as number}/100</span>
                  </div>
                  <Progress value={metrics.overall_score as number} className="h-3" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-600">Maintainability</div>
                    <div className="text-lg font-semibold">{metrics.maintainability as number}/10</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-600">Readability</div>
                    <div className="text-lg font-semibold">{metrics.readability as number}/10</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Issues */}
        {issues && issues.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5" />
                Code Issues ({issues.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <IssueList 
                issues={issues.map(issue => ({
                  title: issue.title as string,
                  description: issue.description as string,
                  severity: issue.severity as 'high' | 'medium' | 'low',
                  file: issue.file as string,
                  line_number: issue.line_number as number
                }))}
                maxItems={5}
              />
            </CardContent>
          </Card>
        )}

        {/* Improvement Suggestions */}
        {suggestions && suggestions.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5" />
                Improvement Suggestions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {suggestions.map((suggestion, index) => (
                  <div key={index} className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                    <div className="font-medium text-green-800 dark:text-green-200">
                      {suggestion.category as string}
                    </div>
                    <div className="text-sm text-green-700 dark:text-green-300 mt-1">
                      {suggestion.description as string}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  const renderQAResults = (data: JsonObject) => {
    const suggestions = data.suggestions as JsonObject[];
    const bestPractices = data.best_practices as JsonObject[];

    return (
      <div className="space-y-6">
        {/* Performance Suggestions */}
        {suggestions && suggestions.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Performance & Quality Suggestions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {suggestions.map((suggestion, index) => (
                  <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                    <div className="font-medium">{suggestion.category as string}</div>
                    <div className="text-sm text-slate-600 mt-1">{suggestion.description as string}</div>
                    {suggestion.impact && (
                      <Badge variant="outline" className="mt-2">
                        Impact: {suggestion.impact as string}
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Best Practices */}
        {bestPractices && bestPractices.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Best Practices</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {bestPractices.map((practice, index) => (
                  <div key={index} className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                    <div className="font-medium">{practice.title as string}</div>
                    <div className="text-sm text-slate-600 mt-1">{practice.description as string}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  const renderGenericResult = (data: JsonObject) => {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Analysis Result</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="bg-slate-100 dark:bg-slate-800 p-4 rounded-md text-sm overflow-auto max-h-96">
            {JSON.stringify(data, null, 2)}
          </pre>
        </CardContent>
      </Card>
    );
  };

  const renderContent = () => {
    if (status === 'failed') {
      return (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-600">
              <AlertCircle className="w-5 h-5" />
              Analysis Failed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-slate-600">{result.error as string || 'An error occurred during analysis'}</p>
          </CardContent>
        </Card>
      );
    }

    // Route to specific visualization based on agent type
    switch (agentId) {
      case 'repository_analyzer':
        return renderRepositoryAnalysis(result);
      case 'code_review_agent':
        return renderCodeReviewResults(result);
      case 'qa_agent':
        return renderQAResults(result);
      default:
        return renderGenericResult(result);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-semibold">{agentName} Results</h3>
        <Badge variant={status === 'failed' ? 'error' : 'success'}>
          {status === 'failed' ? 'Failed' : 'Completed'}
        </Badge>
      </div>
      {renderContent()}
    </div>
  );
};

export default AgentResultVisualization;