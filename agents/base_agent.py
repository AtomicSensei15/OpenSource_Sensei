from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, TYPE_CHECKING, Tuple, Set, Union
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio
import json
import logging
import os
import sys
import tempfile
import shutil
from pathlib import Path
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from .base_agent import AgentOrchestrator

logger = logging.getLogger(__name__)

class AgentStatus(str, Enum):
    """Status states for agents in the system"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"
    INITIALIZING = "initializing"

class MessageType(str, Enum):
    """Types of messages that can be exchanged between agents"""
    TASK = "task"
    RESPONSE = "response"
    ERROR = "error"
    STATUS_UPDATE = "status_update"
    COLLABORATION = "collaboration"
    NOTIFICATION = "notification"
    DATA_REQUEST = "data_request"
    DATA_RESPONSE = "data_response"

@dataclass
class AgentMessage:
    """Message structure for inter-agent communication"""
    id: str
    sender_id: str
    recipient_id: str
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None
    priority: int = 0  # Higher number = higher priority
    ttl: Optional[int] = None  # Time to live in seconds

class AgentCapability(BaseModel):
    """Defines what an agent can do"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    required_resources: List[str] = Field(default_factory=list)
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

class BaseAgent(ABC):
    """Abstract base class for all agents in the system"""
    
    def __init__(self, agent_id: str, name: str, description: str):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.status = AgentStatus.IDLE
        self.capabilities: List[AgentCapability] = []
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.context: Dict[str, Any] = {}
        self.orchestrator: Optional['AgentOrchestrator'] = None
        self.last_activity: datetime = datetime.now()
        self.performance_metrics: Dict[str, Any] = {
            "tasks_completed": 0,
            "success_rate": 0.0,
            "avg_response_time": 0.0,
            "errors": 0
        }
        self.cache: Dict[str, Any] = {}
        self.cache_ttl: int = 3600  # Default cache TTL in seconds
        self.supported_languages: Set[str] = set()
        self.setup_message_handlers()
    
    def setup_message_handlers(self):
        """Set up default message handlers"""
        self.message_handlers = {
            MessageType.TASK: self._handle_task,
            MessageType.COLLABORATION: self._handle_collaboration,
            MessageType.STATUS_UPDATE: self._handle_status_update,
            MessageType.DATA_REQUEST: self._handle_data_request,
            MessageType.NOTIFICATION: self._handle_notification
        }
    
    @abstractmethod
    async def initialize(self):
        """Initialize the agent with necessary resources"""
        pass
    
    @abstractmethod
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task and return results"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[AgentCapability]:
        """Return list of agent capabilities"""
        pass
    
    async def _handle_task(self, message: AgentMessage) -> AgentMessage:
        """Handle incoming task messages"""
        try:
            start_time = datetime.now()
            self.status = AgentStatus.BUSY
            self.last_activity = datetime.now()
            
            result = await self.process_task(message.content)
            
            # Update performance metrics
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            self._update_performance_metrics(True, processing_time)
            
            self.status = AgentStatus.IDLE
            
            return AgentMessage(
                id=f"{message.id}_response",
                sender_id=self.agent_id,
                recipient_id=message.sender_id,
                message_type=MessageType.RESPONSE,
                content={"result": result, "success": True},
                timestamp=datetime.now(),
                correlation_id=message.correlation_id
            )
        except Exception as e:
            self.status = AgentStatus.ERROR
            logger.error(f"Agent {self.agent_id} error processing task: {e}")
            
            # Update performance metrics with failure
            self._update_performance_metrics(False, 0)
            
            return AgentMessage(
                id=f"{message.id}_error",
                sender_id=self.agent_id,
                recipient_id=message.sender_id,
                message_type=MessageType.ERROR,
                content={"error": str(e), "success": False},
                timestamp=datetime.now(),
                correlation_id=message.correlation_id
            )
    
    async def _handle_collaboration(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle collaboration requests from other agents"""
        # Override in subclasses for specific collaboration logic
        logger.info(f"Agent {self.agent_id} received collaboration request from {message.sender_id}")
        self.last_activity = datetime.now()
        return None
    
    async def _handle_status_update(self, message: AgentMessage) -> None:
        """Handle status update messages"""
        logger.info(f"Agent {self.agent_id} received status update: {message.content}")
        self.last_activity = datetime.now()
    
    async def _handle_data_request(self, message: AgentMessage) -> AgentMessage:
        """Handle data request messages from other agents"""
        logger.info(f"Agent {self.agent_id} received data request from {message.sender_id}")
        self.last_activity = datetime.now()
        
        # Default implementation returns empty data
        # Override in subclasses for specific data handling
        return AgentMessage(
            id=f"{message.id}_response",
            sender_id=self.agent_id,
            recipient_id=message.sender_id,
            message_type=MessageType.DATA_RESPONSE,
            content={"data": {}, "success": True},
            timestamp=datetime.now(),
            correlation_id=message.correlation_id
        )
    
    async def _handle_notification(self, message: AgentMessage) -> None:
        """Handle notification messages"""
        logger.info(f"Agent {self.agent_id} received notification: {message.content}")
        self.last_activity = datetime.now()
    
    def _update_performance_metrics(self, success: bool, processing_time: float) -> None:
        """Update agent performance metrics"""
        self.performance_metrics["tasks_completed"] += 1
        
        if success:
            # Update success rate
            current_success = self.performance_metrics["success_rate"] * (self.performance_metrics["tasks_completed"] - 1)
            self.performance_metrics["success_rate"] = (current_success + 1) / self.performance_metrics["tasks_completed"]
            
            # Update average response time
            current_avg_time = self.performance_metrics["avg_response_time"]
            self.performance_metrics["avg_response_time"] = (
                (current_avg_time * (self.performance_metrics["tasks_completed"] - 1) + processing_time) / 
                self.performance_metrics["tasks_completed"]
            )
        else:
            # Update error count and success rate
            self.performance_metrics["errors"] += 1
            current_success = self.performance_metrics["success_rate"] * (self.performance_metrics["tasks_completed"] - 1)
            self.performance_metrics["success_rate"] = current_success / self.performance_metrics["tasks_completed"]
    
    async def send_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Send message through orchestrator"""
        if self.orchestrator:
            return await self.orchestrator.route_message(message)
        logger.warning(f"Agent {self.agent_id} has no orchestrator to send message")
        return None
    
    async def collaborate_with_agent(self, target_agent_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Request collaboration with another agent"""
        message = AgentMessage(
            id=f"collab_{datetime.now().timestamp()}",
            sender_id=self.agent_id,
            recipient_id=target_agent_id,
            message_type=MessageType.COLLABORATION,
            content=request,
            timestamp=datetime.now()
        )
        
        response = await self.send_message(message)
        if response and response.message_type == MessageType.RESPONSE:
            return response.content
        return {"error": "Collaboration failed", "success": False}
    
    async def request_data_from_agent(self, target_agent_id: str, data_request: Dict[str, Any]) -> Dict[str, Any]:
        """Request data from another agent"""
        message = AgentMessage(
            id=f"data_req_{datetime.now().timestamp()}",
            sender_id=self.agent_id,
            recipient_id=target_agent_id,
            message_type=MessageType.DATA_REQUEST,
            content=data_request,
            timestamp=datetime.now()
        )
        
        response = await self.send_message(message)
        if response and response.message_type == MessageType.DATA_RESPONSE:
            return response.content
        return {"error": "Data request failed", "success": False}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        return self.performance_metrics
    
    def set_context(self, context_data: Dict[str, Any]) -> None:
        """Set agent context data"""
        self.context.update(context_data)
    
    def reset_context(self) -> None:
        """Reset agent context to empty"""
        self.context = {}
    
    def add_to_cache(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Add data to agent cache with TTL"""
        expiry = datetime.now().timestamp() + (ttl if ttl is not None else self.cache_ttl)
        self.cache[key] = {
            "data": data,
            "expiry": expiry
        }
    
    def get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache if not expired"""
        if key not in self.cache:
            return None
        
        cache_item = self.cache[key]
        if datetime.now().timestamp() > cache_item["expiry"]:
            # Cache expired
            del self.cache[key]
            return None
        
        return cache_item["data"]
    
    def clear_cache(self) -> None:
        """Clear all cached data"""
        self.cache = {}

class AgentOrchestrator:
    """Orchestrates communication and coordination between agents"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self.workflow_templates: Dict[str, Dict] = {}
        self.event_listeners: Dict[str, List[Callable]] = {}
        self.global_context: Dict[str, Any] = {}
        self.message_history: List[AgentMessage] = []
        self.max_history_size: int = 1000
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent with the orchestrator"""
        agent.orchestrator = self
        self.agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.agent_id}")
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the orchestrator"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.orchestrator = None
            del self.agents[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")
            return True
        return False
    
    async def route_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Route message to appropriate agent"""
        # Store message in history
        self._add_to_message_history(message)
        
        # Trigger event listeners
        self._trigger_event(f"message.{message.message_type.value}", message)
        
        target_agent = self.agents.get(message.recipient_id)
        if not target_agent:
            logger.error(f"Target agent {message.recipient_id} not found")
            return None
        
        handler = target_agent.message_handlers.get(message.message_type)
        if handler:
            response = await handler(message)
            
            # Add response to history if it exists
            if response:
                self._add_to_message_history(response)
                
            return response
        
        logger.warning(f"No handler for message type {message.message_type} in agent {message.recipient_id}")
        return None
    
    def _add_to_message_history(self, message: AgentMessage) -> None:
        """Add message to history with size limit"""
        self.message_history.append(message)
        if len(self.message_history) > self.max_history_size:
            self.message_history = self.message_history[-self.max_history_size:]
    
    def register_event_listener(self, event_name: str, callback: Callable) -> None:
        """Register event listener for a specific event"""
        if event_name not in self.event_listeners:
            self.event_listeners[event_name] = []
        self.event_listeners[event_name].append(callback)
    
    def _trigger_event(self, event_name: str, data: Any) -> None:
        """Trigger registered event listeners"""
        if event_name in self.event_listeners:
            for callback in self.event_listeners[event_name]:
                try:
                    asyncio.create_task(callback(data))
                except Exception as e:
                    logger.error(f"Error in event listener for {event_name}: {e}")
    
    async def execute_workflow(self, workflow_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a predefined workflow involving multiple agents"""
        if workflow_name not in self.workflow_templates:
            raise ValueError(f"Workflow {workflow_name} not found")
        
        workflow = self.workflow_templates[workflow_name]
        results = {}
        
        for step in workflow["steps"]:
            agent_id = step["agent_id"]
            task_data = step["task"]
            
            # Replace placeholders with previous results
            for key, value in task_data.items():
                if isinstance(value, str) and value.startswith("${"):
                    result_key = value[2:-1]
                    task_data[key] = results.get(result_key, value)
            
            message = AgentMessage(
                id=f"workflow_{workflow_name}_{step['name']}",
                sender_id="orchestrator",
                recipient_id=agent_id,
                message_type=MessageType.TASK,
                content=task_data,
                timestamp=datetime.now(),
                correlation_id=workflow_name
            )
            
            response = await self.route_message(message)
            if response and response.content.get("success"):
                results[step["name"]] = response.content["result"]
            else:
                raise Exception(f"Workflow step {step['name']} failed")
        
        return results
    
    def define_workflow(self, name: str, workflow_config: Dict[str, Any]):
        """Define a new workflow template"""
        self.workflow_templates[name] = workflow_config
        logger.info(f"Defined new workflow template: {name}")
    
    async def start(self):
        """Start the orchestrator"""
        self.running = True
        logger.info("Agent orchestrator started")
        
        # Initialize all registered agents
        init_tasks = []
        for agent_id, agent in self.agents.items():
            agent.status = AgentStatus.INITIALIZING
            init_tasks.append(self._initialize_agent(agent))
        
        # Wait for all agents to initialize
        await asyncio.gather(*init_tasks)
    
    async def _initialize_agent(self, agent: BaseAgent):
        """Initialize a single agent"""
        try:
            await agent.initialize()
            agent.status = AgentStatus.IDLE
            logger.info(f"Agent {agent.agent_id} initialized successfully")
        except Exception as e:
            agent.status = AgentStatus.ERROR
            logger.error(f"Failed to initialize agent {agent.agent_id}: {e}")
    
    async def stop(self):
        """Stop the orchestrator"""
        self.running = False
        logger.info("Agent orchestrator stopped")
    
    def get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered agents"""
        return {
            agent_id: {
                "name": agent.name,
                "status": agent.status.value,
                "capabilities": [cap.name for cap in agent.get_capabilities()],
                "last_activity": agent.last_activity.isoformat(),
                "performance": agent.get_performance_metrics()
            }
            for agent_id, agent in self.agents.items()
        }
    
    def get_agent_capabilities(self) -> Dict[str, List[str]]:
        """Get capabilities of all registered agents"""
        return {
            agent_id: [cap.name for cap in agent.get_capabilities()]
            for agent_id, agent in self.agents.items()
        }
    
    def get_workflow_templates(self) -> List[str]:
        """Get list of available workflow templates"""
        return list(self.workflow_templates.keys())
    
    def set_global_context(self, context_data: Dict[str, Any]) -> None:
        """Set global context data available to all agents"""
        self.global_context.update(context_data)
        # Notify agents of context update
        asyncio.create_task(self._broadcast_context_update(context_data))
    
    async def _broadcast_context_update(self, context_data: Dict[str, Any]) -> None:
        """Broadcast context update to all agents"""
        for agent_id, agent in self.agents.items():
            agent.set_context(context_data)
    
    def get_message_history(self, limit: int = 50, message_type: Optional[MessageType] = None,
                           agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get message history with optional filtering"""
        filtered_history = self.message_history
        
        if message_type:
            filtered_history = [m for m in filtered_history if m.message_type == message_type]
        
        if agent_id:
            filtered_history = [m for m in filtered_history 
                               if m.sender_id == agent_id or m.recipient_id == agent_id]
        
        # Return most recent messages first, limited by count
        return [self._message_to_dict(m) for m in filtered_history[-limit:]]
    
    def _message_to_dict(self, message: AgentMessage) -> Dict[str, Any]:
        """Convert AgentMessage to dictionary for external API"""
        return {
            "id": message.id,
            "sender_id": message.sender_id,
            "recipient_id": message.recipient_id,
            "message_type": message.message_type.value,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "correlation_id": message.correlation_id
        }

class TaskResult(BaseModel):
    """Standard task result format"""
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    execution_time: float = 0.0  # Time in seconds
    task_id: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    
    @classmethod
    def success_result(cls, agent_id: str, data: Dict[str, Any], 
                      execution_time: float = 0.0, 
                      metadata: Optional[Dict[str, Any]] = None, 
                      task_id: Optional[str] = None) -> 'TaskResult':
        """Create a successful task result"""
        return cls(
            success=True,
            data=data,
            agent_id=agent_id,
            execution_time=execution_time,
            metadata=metadata or {},
            task_id=task_id
        )
    
    @classmethod
    def error_result(cls, agent_id: str, errors: List[str], 
                    execution_time: float = 0.0,
                    metadata: Optional[Dict[str, Any]] = None, 
                    task_id: Optional[str] = None) -> 'TaskResult':
        """Create an error task result"""
        return cls(
            success=False,
            errors=errors,
            agent_id=agent_id,
            execution_time=execution_time,
            metadata=metadata or {},
            task_id=task_id
        )
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message to the result"""
        self.warnings.append(warning)
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the result"""
        self.metadata[key] = value