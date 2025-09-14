import axios, { AxiosError } from 'axios';

// Generic JSON helpers to avoid widespread `any` usage while allowing flexible backend payloads
export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonObject | JsonArray;
export interface JsonObject { [key: string]: JsonValue }
export type JsonArray = JsonValue[];

// API base configuration
// Allow override through Vite env variable: define VITE_API_BASE_URL in .env (e.g., http://localhost:8000/api/v1)
// Vite injects `import.meta.env` typed as `ImportMetaEnv`; we safely index into it.
const API_BASE_URL: string = (import.meta as ImportMeta).env && (import.meta as ImportMeta).env.VITE_API_BASE_URL
  ? (import.meta as ImportMeta).env.VITE_API_BASE_URL
  : 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types matching the backend schemas
export interface Project {
  id: string;
  name: string;
  description?: string;
  project_type: 'github_repo' | 'local_repo' | 'archive_file' | 'single_file';
  status: 'created' | 'analyzing' | 'completed' | 'failed' | 'cancelled';
  source_url?: string;
  source_path?: string;
  repository_name?: string;
  repository_owner?: string;
  branch?: string;
  analysis_config?: JsonObject;
  include_patterns?: string[];
  exclude_patterns?: string[];
  total_files: number;
  total_lines: number;
  languages_detected?: JsonObject;
  technologies_detected?: JsonObject;
  progress_percentage: number;
  current_phase?: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  file_size_bytes?: number;
  user_id?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface Analysis {
  id: string;
  name: string;
  description?: string;
  analysis_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  project_id: string;
  agent_id?: string;
  agent_type?: string;
  config?: JsonObject;
  parameters?: JsonObject;
  results?: JsonObject;
  summary?: string;
  recommendations?: Array<JsonObject>;
  confidence_score?: number;
  quality_score?: number;
  progress_percentage: number;
  current_step?: string;
  total_steps?: number;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  execution_time_seconds?: number;
  files_processed: number;
  files_total?: number;
  files_skipped: number;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface Agent {
  id: string;
  name: string;
  agent_type: string;
  status: 'idle' | 'busy' | 'error' | 'offline' | 'initializing';
  description?: string;
  capabilities?: Array<JsonObject>;
  config?: JsonObject;
  performance_metrics?: JsonObject;
  last_activity?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
  project_type: 'github_repo' | 'local_repo' | 'archive_file' | 'single_file';
  source_url?: string;
  analysis_config?: JsonObject;
  include_patterns?: string[];
  exclude_patterns?: string[];
  branch?: string;
}

export interface CreateAnalysisRequest {
  name: string;
  description?: string;
  analysis_type: string;
  config?: JsonObject;
  parameters?: JsonObject;
}

// API Service functions
const apiService = {
  // Health check
  async healthCheck() {
    const response = await api.get('/health');
    return response.data;
  },

  // Projects
  async createProject(data: CreateProjectRequest): Promise<Project> {
    try {
      const response = await api.post('/projects/', data);
      return response.data;
    } catch (err) {
      handleApiError(err, 'Failed to create project');
    }
  },
  
  async getProjects(params?: { skip?: number; limit?: number; name?: string; project_status?: string }): Promise<PaginatedResponse<Project>> {
    try {
      const response = await api.get('/projects/', { params });
      return response.data;
    } catch (err) {
      handleApiError(err, 'Failed to fetch projects');
    }
  },
  
  async getProject(id: string): Promise<Project> {
    try {
      const response = await api.get(`/projects/${id}`);
      return response.data;
    } catch (err) {
      handleApiError(err, 'Failed to fetch project');
    }
  },

  // Analyses
  async createAnalysis(data: CreateAnalysisRequest): Promise<Analysis> {
    try {
      const response = await api.post('/analyses/', data);
      return response.data;
    } catch (err) {
      handleApiError(err, 'Failed to create analysis');
    }
  },
  
  async getAnalyses(params?: { skip?: number; limit?: number; project_id?: string; analysis_status?: string }): Promise<PaginatedResponse<Analysis>> {
    try {
      const response = await api.get('/analyses/', { params });
      return response.data;
    } catch (err) {
      handleApiError(err, 'Failed to fetch analyses');
    }
  },
  
  async getAnalysis(id: string): Promise<Analysis> {
    try {
      const response = await api.get(`/analyses/${id}`);
      return response.data;
    } catch (err) {
      handleApiError(err, 'Failed to fetch analysis');
    }
  },

  // Agents
  async getAgents(params?: { skip?: number; limit?: number; agent_type?: string; agent_status?: string }): Promise<PaginatedResponse<Agent>> {
    try {
      const response = await api.get('/agents/', { params });
      return response.data;
    } catch (err) {
      handleApiError(err, 'Failed to fetch agents');
    }
  },
  
  async getAgent(id: string): Promise<Agent> {
    try {
      const response = await api.get(`/agents/${id}`);
      return response.data;
    } catch (err) {
      handleApiError(err, 'Failed to fetch agent');
    }
  },
};

// Simple runtime connectivity probe (can be used in components or console)
export async function probeApiHealth(): Promise<{ ok: boolean; data?: unknown; error?: string }> {
  try {
    const { data } = await api.get('/health');
    return { ok: true, data };
  } catch (e) {
    const err = e as Error;
    return { ok: false, error: err.message };
  }
}

// Centralized error handler throws a standard Error so callers can catch & surface UI toast
function handleApiError(err: unknown, fallbackMessage: string): never {
  if (axios.isAxiosError(err)) {
  const axErr = err as AxiosError<{ detail?: string }>;
    const detail = axErr.response?.data?.detail || axErr.message;
    throw new Error(`${fallbackMessage}: ${detail}`);
  }
  throw new Error(fallbackMessage);
}

export { apiService };
export default apiService;