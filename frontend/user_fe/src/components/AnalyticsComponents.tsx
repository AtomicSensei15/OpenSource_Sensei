import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, CheckCircle2, Info, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon: React.ReactNode;
  color: string;
}


const MetricCard: React.FC<MetricCardProps> = ({ title, value, change, icon, color }) => {
  const getTrendIcon = () => {
    if (change === undefined) return null;
    if (change > 0) return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (change < 0) return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-slate-400" />;
  };

  return (
    <Card className="relative overflow-hidden">
      <div className={`absolute top-0 left-0 w-full h-1 ${color}`} />
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="text-sm font-medium text-slate-600 dark:text-slate-400">{title}</div>
          <div className="text-slate-400">{icon}</div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-end justify-between">
          <div className="text-2xl font-bold">{value}</div>
          {change !== undefined && (
            <div className="flex items-center gap-1 text-sm">
              {getTrendIcon()}
              <span className={change > 0 ? 'text-green-500' : change < 0 ? 'text-red-500' : 'text-slate-400'}>
                {change > 0 ? '+' : ''}{change}%
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

interface IssueListProps {
  issues: Array<{
    title: string;
    description: string;
    severity: 'high' | 'medium' | 'low' | string;
    file?: string;
    line_number?: number;
  }>;
  maxItems?: number;
}

const IssueList: React.FC<IssueListProps> = ({ issues, maxItems = 5 }) => {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-slate-100 text-slate-800 border-slate-200';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high': return <AlertTriangle className="w-4 h-4" />;
      case 'medium': return <Info className="w-4 h-4" />;
      case 'low': return <CheckCircle2 className="w-4 h-4" />;
      default: return <Info className="w-4 h-4" />;
    }
  };

  return (
    <div className="space-y-3">
      {issues.slice(0, maxItems).map((issue, index) => (
        <div key={index} className="border rounded-lg p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <Badge className={`${getSeverityColor(issue.severity)} text-xs px-2 py-1`}>
                  <div className="flex items-center gap-1">
                    {getSeverityIcon(issue.severity)}
                    {issue.severity.toUpperCase()}
                  </div>
                </Badge>
              </div>
              <h4 className="font-medium text-slate-900 dark:text-slate-100 mb-1">
                {issue.title}
              </h4>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                {issue.description}
              </p>
              {issue.file && (
                <div className="text-xs text-slate-500 font-mono bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                  {issue.file}{issue.line_number ? `:${issue.line_number}` : ''}
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
      {issues.length > maxItems && (
        <div className="text-center py-3 text-sm text-slate-500 border-t">
          +{issues.length - maxItems} more issues
        </div>
      )}
    </div>
  );
};

interface ChartContainerProps {
  title: string;
  children: React.ReactElement;
  height?: number;
}

const ChartContainer: React.FC<ChartContainerProps> = ({ title, children }) => (
  <Card>
    <CardHeader>
      <CardTitle className="text-lg">{title}</CardTitle>
    </CardHeader>
    <CardContent>{children}</CardContent>
  </Card>
);

// Custom color palettes
const COLORS = ['#3b82f6', '#ef4444', '#f59e0b', '#10b981', '#8b5cf6', '#f97316', '#06b6d4', '#84cc16'];

interface LanguageDataRecord { bytes?: number; lines?: number; percentage?: number; file_count?: number }
interface LanguageStatsProps {
  data: Record<string, LanguageDataRecord> | null | undefined;
  title?: string;
  showBytes?: boolean; // if true, display both lines and bytes
  maxRows?: number;
}

// Utility to format large numbers
const formatNumber = (n: number): string => {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'k';
  return n.toString();
};

const LanguageStats: React.FC<LanguageStatsProps> = ({ data, title = 'Language Distribution', showBytes = true, maxRows = 20 }) => {
  if (!data || Object.keys(data).length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-slate-500">No language data available.</div>
        </CardContent>
      </Card>
    );
  }

  const entries = Object.entries(data).map(([lang, stats]) => ({
    name: lang,
    lines: stats.lines ?? 0,
    bytes: stats.bytes ?? 0,
    percentage: stats.percentage ?? 0,
    file_count: stats.file_count ?? 0
  })).filter(e => e.lines > 0 || e.bytes > 0)
    .sort((a, b) => b.percentage - a.percentage);

  const totalLines = entries.reduce((acc, cur) => acc + cur.lines, 0);
  const totalBytes = entries.reduce((acc, cur) => acc + cur.bytes, 0);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle className="text-lg">{title}</CardTitle>
          <div className="text-xs text-slate-500 space-x-3 font-medium">
            <span>Total LOC: {formatNumber(totalLines)}</span>
            {showBytes && <span>Total Bytes: {formatNumber(totalBytes)}</span>}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {entries.slice(0, maxRows).map((e, i) => {
          const barPct = e.percentage; // already percentage from backend (lines based)
          return (
            <div key={e.name} className="space-y-1">
              <div className="flex items-center gap-2 text-xs font-medium">
                <span className="inline-flex items-center gap-1">
                  <span className="inline-block w-3 h-3 rounded-sm" style={{ background: COLORS[i % COLORS.length] }} />
                  {e.name}
                </span>
                <span className="ml-auto tabular-nums text-slate-500">{barPct.toFixed(2)}%</span>
              </div>
              <div className="w-full h-3 bg-slate-100 dark:bg-slate-800 rounded overflow-hidden">
                <div
                  className="h-full transition-all"
                  style={{ width: `${barPct}%`, background: COLORS[i % COLORS.length] }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>{formatNumber(e.lines)} LOC</span>
                {showBytes && <span>{formatNumber(e.bytes)} bytes</span>}
                <span>{e.file_count} files</span>
              </div>
            </div>
          );
        })}
        {entries.length > maxRows && (
          <div className="text-xs text-slate-500">+{entries.length - maxRows} more languages</div>
        )}
      </CardContent>
    </Card>
  );
};

interface FileIssue {
  title: string;
  description: string;
  severity: 'high' | 'medium' | 'low' | string;
  file_path?: string;
  line_number?: number;
}

interface FileSummaryCardProps {
  file: {
    file_path: string;
    quality_score: number;
    issues: FileIssue[];
    metrics: {
      lines_of_code: number;
      complexity: number;
      functions: number;
      classes: number;
      docstring_coverage: number;
    };
  };
}

const FileSummaryCard: React.FC<FileSummaryCardProps> = ({ file }) => {
  return (
    <Card className="mb-4">
      <CardHeader>
        <CardTitle className="text-lg flex items-center justify-between">
          <span className="truncate">{file.file_path.split('/').pop()}</span>
          <Badge variant={file.quality_score > 80 ? 'success' : file.quality_score > 50 ? 'warning' : 'destructive'}>
            Score: {file.quality_score}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 text-center">
          <div>
            <p className="text-sm text-slate-500">Lines of Code</p>
            <p className="text-lg font-bold">{file.metrics.lines_of_code}</p>
          </div>
          <div>
            <p className="text-sm text-slate-500">Complexity</p>
            <p className="text-lg font-bold">{file.metrics.complexity}</p>
          </div>
          <div>
            <p className="text-sm text-slate-500">Functions</p>
            <p className="text-lg font-bold">{file.metrics.functions}</p>
          </div>
          <div>
            <p className="text-sm text-slate-500">Classes</p>
            <p className="text-lg font-bold">{file.metrics.classes}</p>
          </div>
        </div>
        {file.issues.length > 0 && (
          <div>
            <h4 className="font-semibold mb-2">Issues:</h4>
            <IssueList issues={file.issues.map(issue => ({
              title: issue.title,
              description: issue.description,
              severity: issue.severity,
              file: issue.file_path,
              line_number: issue.line_number,
            }))} maxItems={5} />
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export { MetricCard, IssueList, ChartContainer, COLORS, LanguageStats, FileSummaryCard };