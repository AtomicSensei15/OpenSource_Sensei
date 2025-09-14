from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import uuid
import logging
import tempfile
import shutil
import os
from git import Repo

# It's better to place schemas in a separate file, but for simplicity here, we define them.
# In your project, you'd use `from app.schemas import ...`
from pydantic import BaseModel
from typing import List, Dict, Any

class AnalysisRequest(BaseModel):
    repo_url: str
class AvailableAgent(BaseModel):
    name: str
    description: str
    agent_id: str
class InitialAnalysisResponse(BaseModel):
    analysis_id: str
    repo_url: str
    message: str
    available_agents: List[AvailableAgent]
    initial_summary: Dict[str, Any]
class AgentAnalysisResponse(BaseModel):
    analysis_id: str
    agent_id: str
    status: str
    result: Dict[str, Any]


# Assuming agents are in an 'agents' directory relative to 'backend'
# This path adjustment might be needed depending on how you run the app
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from agents.repository_analyzer import RepositoryAnalysisAgent
from agents.code_review_agent import CodeReviewAgent
from agents.qa_agent import QAAgent
from agents.research_agent import ResearchAgent

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage for analysis sessions
analysis_store: Dict[str, Dict[str, Any]] = {}

# Instantiate agents
repo_analyzer = RepositoryAnalysisAgent()
code_reviewer = CodeReviewAgent()
qa_agent = QAAgent()
research_agent = ResearchAgent()
# Differentiate the second CodeReviewAgent for security scans
code_reviewer_security = CodeReviewAgent()
code_reviewer_security.name = "Security Code Review Agent"

AVAILABLE_AGENTS_MAP = {
    "repo_analyzer": {
        "instance": repo_analyzer,
        "description": "Examines project structure and architectural patterns."
    },
    "code_reviewer": {
        "instance": code_reviewer,
        "description": "Performs deep code quality analysis and style checks."
    },
    "qa_agent": {
        "instance": qa_agent,
        "description": "Suggests improvements and best practices based on a sample file."
    },
    "research_agent": {
        "instance": research_agent,
        "description": "Researches programming topics and provides documentation insights."
    },
}

@router.post("/analyze", response_model=InitialAnalysisResponse)
async def start_analysis(request: AnalysisRequest):
    """
    Accepts a GitHub repository URL, clones it, performs an initial analysis,
    and returns an analysis ID with available agents for further actions.
    """
    analysis_id = str(uuid.uuid4())
    temp_dir = tempfile.mkdtemp(prefix="sensei_")
    logger.info(f"Starting analysis for {request.repo_url} with ID: {analysis_id}")

    try:
        logger.info(f"Cloning {request.repo_url} into {temp_dir}")
        Repo.clone_from(request.repo_url, temp_dir)

        initial_result = await repo_analyzer._analyze_local_repository(temp_dir)

        analysis_store[analysis_id] = {
            "repo_url": request.repo_url,
            "local_path": temp_dir,
            "initial_summary": initial_result
        }

        available_agents = [
            AvailableAgent(name=agent["instance"].name, description=agent["description"], agent_id=agent_id)
            for agent_id, agent in AVAILABLE_AGENTS_MAP.items()
        ]

        return InitialAnalysisResponse(
            analysis_id=analysis_id,
            repo_url=request.repo_url,
            message="Initial analysis complete. Select an agent for deeper insights.",
            available_agents=available_agents,
            initial_summary=initial_result
        )
    except Exception as e:
        logger.error(f"Failed initial analysis for {request.repo_url}: {e}", exc_info=True)
        shutil.rmtree(temp_dir, ignore_errors=True)
        if analysis_id in analysis_store:
            del analysis_store[analysis_id]
        raise HTTPException(status_code=500, detail=f"Failed to analyze repository: {e}")

@router.post("/analyze/{analysis_id}/{agent_id}", response_model=AgentAnalysisResponse)
async def run_agent_analysis(analysis_id: str, agent_id: str):
    """
    Runs a specific agent on a previously analyzed repository.
    """
    if analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Analysis ID not found.")
    
    if agent_id not in AVAILABLE_AGENTS_MAP:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")

    analysis_session = analysis_store[analysis_id]
    local_repo_path = analysis_session.get("local_path")
    if not local_repo_path:
        raise HTTPException(status_code=500, detail="Repository path not found in analysis session.")
    agent_instance = AVAILABLE_AGENTS_MAP[agent_id]["instance"]
    logger.info(f"Running agent '{agent_id}' on analysis '{analysis_id}'")

    try:
        task_result = {}
        if agent_id == "repo_analyzer":
            task_result = analysis_session["initial_summary"]
        elif agent_id in ["code_reviewer", "security_scan"]:
            all_files, file_results = [], []
            for root, _, files in os.walk(local_repo_path):
                if ".git" in root: continue
                for file in files: all_files.append(os.path.join(root, file))
            
            for file_path in all_files[:20]: # Limit for demo
                 try:
                     with open(file_path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
                     lang = agent_instance._detect_language(file_path)
                     if lang: file_results.append(await agent_instance._analyze_file_quality(file_path, content, lang))
                 except Exception: continue
            task_result = {"files_analyzed": len(file_results), "results": file_results}
        elif agent_id == "qa_agent":
            sample_code, sample_lang, sample_file_path = "", "", "No suitable file found"
            
            # Simple language detection function
            def detect_language(file_path: str) -> str:
                ext = os.path.splitext(file_path)[1].lower()
                language_map = {
                    '.py': 'python',
                    '.js': 'javascript', 
                    '.jsx': 'javascript',
                    '.ts': 'typescript',
                    '.tsx': 'typescript',
                    '.java': 'java',
                    '.cpp': 'cpp',
                    '.c': 'c',
                    '.cs': 'csharp',
                    '.go': 'go',
                    '.rs': 'rust',
                    '.php': 'php',
                    '.rb': 'ruby',
                    '.kt': 'kotlin',
                    '.swift': 'swift'
                }
                return language_map.get(ext, 'unknown')
            
            for root, _, files in os.walk(local_repo_path):
                 if ".git" in root: continue
                 for file in files:
                     if file.endswith((".py", ".js", ".ts")):
                         sample_file_path = os.path.join(root, file)
                         with open(sample_file_path, 'r', encoding='utf-8') as f: sample_code = f.read()
                         sample_lang = detect_language(sample_file_path)
                         break
                 if sample_code: break
            
            if sample_code and sample_lang:
                task_result = await qa_agent._suggest_improvements(code=sample_code, language=sample_lang)
                task_result["analyzed_file"] = os.path.relpath(sample_file_path, local_repo_path)
            else:
                task_result = {"message": "Could not find a suitable file to generate QA suggestions."}
        elif agent_id == "research_agent":
            # Use the research agent to provide insights about the repository
            research_task = {
                "task_type": "research_best_practices",
                "language": "python",  # Default, could be detected from repo
                "topic": "code analysis and best practices"
            }
            task_result = await research_agent.process_task(research_task)
        else:
            task_result = {"message": f"No specific handling implemented for agent: {agent_id}"}

        return AgentAnalysisResponse(analysis_id=analysis_id, agent_id=agent_id, status="completed", result=task_result)
    except Exception as e:
        logger.error(f"Agent '{agent_id}' failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent analysis failed: {e}")
