import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { AlertCircle, FileText, GitBranch, Star, Code, ChevronDown } from 'lucide-react';
import { MetricCard, COLORS, LanguageStats } from './AnalyticsComponents';
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
  // Local helper component for code review file summaries (previously imported)
  interface IssueItem { severity?: string; title?: string; description?: string }
  interface FileResult { file_path?: string; path?: string; quality_score?: number; issues?: IssueItem[] }

  const FileSummaryCard: React.FC<{ file: FileResult }> = ({ file }) => {
    const issues = file.issues || [];
    return (
      <Card className="mb-4">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-mono break-all flex items-center justify-between">
            <span>{file.file_path || file.path || 'Unknown file'}</span>
            {typeof file.quality_score === 'number' && (
              <span className="text-xs font-normal text-slate-500">Score: {file.quality_score}</span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {issues.length > 0 ? (
            <ul className="space-y-1">
              {issues.map((iss: IssueItem, i: number) => (
                <li key={i} className="text-xs flex gap-2">
                  <span className={`px-1 rounded bg-slate-200 dark:bg-slate-700 ${iss.severity === 'high' ? 'bg-red-500/20 text-red-700 dark:text-red-300' : iss.severity === 'medium' ? 'bg-yellow-400/20 text-yellow-700 dark:text-yellow-300' : 'bg-blue-500/20 text-blue-700 dark:text-blue-300'}`}>{iss.severity || 'info'}</span>
                  <span className="flex-1">{iss.title || iss.description}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-slate-500">No issues.</p>
          )}
        </CardContent>
      </Card>
    );
  };

  const renderRepositoryAnalysis = (data: JsonObject) => {
    const structure = data.structure as JsonObject | undefined;
    const languagesBlock = data.languages as JsonObject | undefined;
    const fileSummary = structure?.file_summary as JsonObject | undefined;
    const fileTypes = fileSummary?.file_types as JsonObject | undefined;
    const languagesMap = (languagesBlock?.languages as JsonObject) || {};
    const projectType = (data.metadata as JsonObject | undefined)?.project_type as string | undefined;
    const totalLines = (languagesBlock?.total_lines as number) || 0;

    const dependencies = data.dependencies as JsonObject | undefined;
    const depStats = dependencies?.stats as JsonObject | undefined;
    const directDeps = dependencies?.dependencies as JsonObject | undefined;
    const devDeps = dependencies?.dev_dependencies as JsonObject | undefined;
    const securityIssues = (dependencies?.security_issues as JsonObject[]) || [];
    const packageManagers = (dependencies?.package_managers as string[]) || [];

    const largestFiles = (structure?.file_summary as any)?.largest_files as Array<{ name: string; size: number; path: string }>; // eslint-disable-line @typescript-eslint/no-explicit-any
    const architecturePatterns = (structure?.architecture_patterns as string[]) || [];

    return (
      <div className="space-y-8">
        {/* Repository Stats */}
        <div>
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <GitBranch className="w-5 h-5" />
            Repository Statistics
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
            <MetricCard title="Files" value={(fileSummary?.total_files as number) || 0} icon={<FileText className="w-5 h-5" />} color="bg-blue-500" />
            <MetricCard title="Dirs" value={(fileSummary?.total_directories as number) || 0} icon={<FileText className="w-5 h-5" />} color="bg-indigo-500" />
            <MetricCard title="LOC" value={totalLines.toLocaleString()} icon={<Code className="w-5 h-5" />} color="bg-green-500" />
            <MetricCard title="Code Size" value={((languagesBlock?.total_code_size as number) || 0).toLocaleString()} icon={<Code className="w-5 h-5" />} color="bg-purple-500" />
            <MetricCard title="Primary" value={(languagesBlock?.primary_language as string) || 'N/A'} icon={<Code className="w-5 h-5" />} color="bg-yellow-500" />
            <MetricCard title="Type" value={projectType || 'Unknown'} icon={<GitBranch className="w-5 h-5" />} color="bg-rose-500" />
          </div>
        </div>

        {/* Dependency Metrics */}
        {dependencies && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
              <Code className="w-5 h-5" /> Dependencies
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
              <MetricCard title="Managers" value={packageManagers.length} icon={<Code className="w-5 h-5" />} color="bg-slate-500" />
              <MetricCard title="Direct Deps" value={(depStats?.direct_dependencies as number) || (directDeps ? Object.keys(directDeps).length : 0)} icon={<Code className="w-5 h-5" />} color="bg-teal-500" />
              <MetricCard title="Dev Deps" value={(depStats?.dev_dependencies as number) || (devDeps ? Object.keys(devDeps).length : 0)} icon={<Code className="w-5 h-5" />} color="bg-cyan-500" />
              <MetricCard title="Total Deps" value={(depStats?.total_dependencies as number) || 0} icon={<Code className="w-5 h-5" />} color="bg-emerald-500" />
              <MetricCard title="Sec Issues" value={securityIssues.length} icon={<AlertCircle className="w-5 h-5" />} color={securityIssues.length ? 'bg-red-500' : 'bg-green-600'} />
              <MetricCard title="Managers" value={packageManagers.join(', ') || '—'} icon={<GitBranch className="w-5 h-5" />} color="bg-slate-700" />
            </div>

            {/* Top Dependencies */}
            {directDeps && Object.keys(directDeps).length > 0 && (
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">Top Dependencies</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {Object.entries(directDeps).slice(0, 15).map(([name, version]) => (
                    <div key={name} className="flex items-center text-xs font-mono gap-2">
                      <span className="inline-block px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">{name}</span>
                      <span className="text-slate-500">{version as string}</span>
                    </div>
                  ))}
                  {Object.keys(directDeps).length > 15 && (
                    <div className="text-[10px] text-slate-500">+{Object.keys(directDeps).length - 15} more</div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Security Issues */}
            {securityIssues.length > 0 && (
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">Security Issues</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {securityIssues.slice(0, 10).map((issue: any, idx: number) => { // eslint-disable-line @typescript-eslint/no-explicit-any
                    return (
                      <div key={idx} className="p-2 rounded border text-xs space-y-1 bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-800">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-red-600 dark:text-red-400">{issue.package || issue.name}</span>
                          {issue.version && <span className="text-slate-500">{issue.version}</span>}
                          {issue.severity && <Badge variant="destructive" className="ml-auto text-[10px]">{issue.severity}</Badge>}
                        </div>
                        {issue.description && <div className="text-slate-600 dark:text-slate-400">{issue.description}</div>}
                      </div>
                    );
                  })}
                  {securityIssues.length > 10 && <div className="text-[10px] text-slate-500">+{securityIssues.length - 10} more</div>}
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Architecture Patterns */}
        {architecturePatterns.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Architecture Patterns</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              {architecturePatterns.map(p => (
                <Badge key={p} className="bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800 text-xs px-2 py-1">{p}</Badge>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Languages Distribution */}
        {languagesMap && Object.keys(languagesMap).length > 0 && (
          <LanguageStats data={languagesMap as Record<string, { bytes?: number; lines?: number; percentage?: number; file_count?: number }>} />
        )}

        {/* Lines per Language */}
        {languagesBlock?.lines_per_language && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Lines per Language</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {Object.entries(languagesBlock.lines_per_language as Record<string, number>).map(([lang, lines], idx) => {
                const pct = totalLines ? (lines as number) / totalLines * 100 : 0;
                return (
                  <div key={lang} className="space-y-1">
                    <div className="flex items-center text-xs font-medium gap-2">
                      <span className="inline-flex items-center gap-1">
                        <span className="inline-block w-3 h-3 rounded-sm" style={{ background: COLORS[idx % COLORS.length] }} />
                        {lang}
                      </span>
                      <span className="ml-auto tabular-nums text-slate-500">{pct.toFixed(1)}%</span>
                    </div>
                    <div className="w-full h-2 bg-slate-100 dark:bg-slate-800 rounded">
                      <div className="h-full" style={{ width: `${pct}%`, background: COLORS[idx % COLORS.length] }} />
                    </div>
                    <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                      <span>{(lines as number).toLocaleString()} LOC</span>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        )}

        {/* Largest Files */}
        {largestFiles && largestFiles.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Largest Files</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {largestFiles.map((f, idx) => (
                <div key={f.path} className="flex items-center gap-2 text-xs font-mono">
                  <span className="inline-block w-5 text-right text-slate-500">{idx + 1}.</span>
                  <span className="truncate flex-1" title={f.path}>{f.path}</span>
                  <span className="text-slate-500">{(f.size / 1024).toFixed(1)} KB</span>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* File Types Distribution (list) */}
        {fileTypes && Object.keys(fileTypes).length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">File Types Distribution</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {Object.entries(fileTypes)
                .sort((a, b) => (b[1] as number) - (a[1] as number))
                .map(([ext, count], idx) => {
                  const total = Object.values(fileTypes).reduce((acc: number, v) => acc + (v as number), 0);
                  const pct = total ? ((count as number) / total) * 100 : 0;
                  return (
                    <div key={ext} className="space-y-1">
                      <div className="flex items-center text-xs font-medium gap-2">
                        <span className="inline-flex items-center gap-1">
                          <span className="inline-block w-3 h-3 rounded-sm" style={{ background: COLORS[idx % COLORS.length] }} />
                          {ext || 'unknown'}
                        </span>
                        <span className="ml-auto tabular-nums text-slate-500">{pct.toFixed(1)}%</span>
                      </div>
                      <div className="w-full h-2 bg-slate-100 dark:bg-slate-800 rounded">
                        <div className="h-full" style={{ width: `${pct}%`, background: COLORS[idx % COLORS.length] }} />
                      </div>
                      <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                        <span>{count as number}</span>
                      </div>
                    </div>
                  );
                })}
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  const renderCodeReviewResults = (data: JsonObject) => {
    const filesAnalyzed = (data.files_analyzed as number) || 0;
  const results = (data.results as FileResult[]) || [];
    const totalScore = results.reduce((acc, file) => acc + (file.quality_score || 0), 0);
    const averageScore = filesAnalyzed > 0 ? Math.round(totalScore / filesAnalyzed) : 0;
    const totalIssues = results.reduce((acc, file) => acc + (file.issues?.length || 0), 0);

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <MetricCard title="Files Analyzed" value={filesAnalyzed} icon={<FileText />} color="bg-blue-500" />
            <MetricCard title="Average Quality Score" value={`${averageScore}/100`} icon={<Star />} color="bg-green-500" />
            <MetricCard title="Total Issues Found" value={totalIssues} icon={<AlertCircle />} color="bg-red-500" />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Overall Quality Score</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
                <span className="font-bold text-2xl">{averageScore}</span>
                <Progress value={averageScore} className="w-full h-4" />
            </div>
          </CardContent>
        </Card>

        <details open className="rounded-md bg-slate-100 dark:bg-slate-800">
          <summary className="cursor-pointer list-none flex items-center justify-between p-4 font-semibold text-lg">
            <span>File-by-File Analysis ({results.length} files)</span>
            <ChevronDown className="w-5 h-5" />
          </summary>
          <div className="px-4 pb-4 space-y-2">
            {results.length > 0 ? (
              results.map((file, index) => (
                <FileSummaryCard key={index} file={file} />
              ))
            ) : (
              <p className="text-slate-500 p-4 text-center">No files were analyzed.</p>
            )}
          </div>
        </details>
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
      case 'repo_analyzer':
        return renderRepositoryAnalysis(result);
      case 'code_reviewer':
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
        <Badge variant={status === 'failed' ? 'destructive' : 'success'}>
          {status === 'failed' ? 'Failed' : 'Completed'}
        </Badge>
      </div>
      {renderContent()}
    </div>
  );
};

export default AgentResultVisualization;