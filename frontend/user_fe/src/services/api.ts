import axios, { AxiosError } from 'axios';

// --- Generic Types ---
export type JsonValue = string | number | boolean | null | JsonObject | JsonValue[];
export type JsonObject = { [key: string]: JsonValue };

// --- API Configuration ---
const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});


// --- Request & Response Schemas ---
export interface AnalysisRequest {
  repo_url: string;
}

export interface AvailableAgent {
  name: string;
  description: string;
  agent_id: string;
}

export interface InitialAnalysisResponse {
  analysis_id: string;
  repo_url: string;
  message: string;
  available_agents: AvailableAgent[];
  initial_summary: JsonObject;
}

export interface AgentAnalysisResponse {
  analysis_id: string;
  agent_id: string;
  status: string;
  result: JsonObject;
}


// --- API Service ---
const apiService = {
  async startAnalysis(data: AnalysisRequest): Promise<InitialAnalysisResponse> {
    try {
      const response = await api.post('/analyze', data);
      return response.data;
    } catch (err) {
      handleApiError(err, 'Failed to start analysis');
    }
  },

  async runAgentAnalysis(analysisId: string, agentId: string): Promise<AgentAnalysisResponse> {
    try {
      const response = await api.post(`/analyze/${analysisId}/${agentId}`);
      return response.data;
    } catch (err) {
      handleApiError(err, `Failed to run agent ${agentId}`);
    }
  },
};


// --- Error Handling ---
function handleApiError(err: unknown, fallbackMessage: string): never {
  let message = fallbackMessage;
  if (axios.isAxiosError(err)) {
    const axiosError = err as AxiosError<{ detail?: string }>;
    message = axiosError.response?.data?.detail || axiosError.message || fallbackMessage;
  } else if (err instanceof Error) {
    message = err.message;
  }
  console.error(fallbackMessage, err);
  throw new Error(message);
}

export default apiService;
