"""
Agent service for managing AI agents.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId

from ..models.agent import Agent, AgentStatus, AgentType
from ..models.task import Task, TaskStatus
from .base_service import BaseService, NotFoundError, ValidationError
from ..core.logging import get_logger

logger = get_logger(__name__)


class AgentService(BaseService[Agent]):
    """Service for managing agents."""
    
    def __init__(self):
        super().__init__(Agent)
    
    async def register_agent(
        self,
        name: str,
        agent_type: AgentType,
        description: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        supported_tasks: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
        max_concurrent_tasks: int = 1,
        host: Optional[str] = None,
        port: Optional[int] = None
    ) -> Agent:
        """Register a new agent."""
        try:
            # Check if agent with same name already exists
            existing = await Agent.find_one(Agent.name == name)
            if existing:
                raise ValidationError(f"Agent with name '{name}' already exists")
            
            # Create agent
            agent = await self.create(
                name=name,
                description=description,
                agent_type=agent_type,
                capabilities=capabilities or [],
                supported_tasks=supported_tasks or [],
                config=config or {},
                max_concurrent_tasks=max_concurrent_tasks,
                host=host,
                port=port,
                status=AgentStatus.OFFLINE
            )
            
            logger.info(f"Registered agent: {agent.name} (ID: {agent.id})")
            return agent
            
        except Exception as e:
            logger.error(f"Error registering agent: {e}")
            raise
    
    async def agent_heartbeat(
        self,
        agent_id: ObjectId,
        status: Optional[AgentStatus] = None,
        resource_usage: Optional[Dict[str, float]] = None
    ) -> Agent:
        """Update agent heartbeat and status."""
        agent = await self.get_by_id(agent_id)
        if not agent:
            raise NotFoundError(f"Agent {agent_id} not found")
        
        try:
            # Update heartbeat
            await agent.update_heartbeat()
            
            # Update status if provided
            if status:
                agent.status = status
            
            # Update resource usage if provided
            if resource_usage:
                await agent.update_resource_usage(
                    cpu_percent=resource_usage.get('cpu_percent'),
                    memory_mb=resource_usage.get('memory_mb'),
                    disk_mb=resource_usage.get('disk_mb')
                )
            
            return agent
            
        except Exception as e:
            logger.error(f"Error updating agent heartbeat for {agent_id}: {e}")
            raise
    
    async def mark_agent_online(self, agent_id: ObjectId) -> Agent:
        """Mark agent as online."""
        agent = await self.get_by_id(agent_id)
        if not agent:
            raise NotFoundError(f"Agent {agent_id} not found")
        
        try:
            await agent.mark_online()
            logger.info(f"Agent {agent.name} marked as online")
            return agent
            
        except Exception as e:
            logger.error(f"Error marking agent {agent_id} as online: {e}")
            raise
    
    async def mark_agent_offline(self, agent_id: ObjectId) -> Agent:
        """Mark agent as offline."""
        agent = await self.get_by_id(agent_id)
        if not agent:
            raise NotFoundError(f"Agent {agent_id} not found")
        
        try:
            await agent.mark_offline()
            logger.info(f"Agent {agent.name} marked as offline")
            return agent
            
        except Exception as e:
            logger.error(f"Error marking agent {agent_id} as offline: {e}")
            raise
    
    async def report_agent_error(
        self,
        agent_id: ObjectId,
        error_message: str
    ) -> Agent:
        """Report an agent error."""
        agent = await self.get_by_id(agent_id)
        if not agent:
            raise NotFoundError(f"Agent {agent_id} not found")
        
        try:
            await agent.mark_error(error_message)
            logger.error(f"Agent {agent.name} reported error: {error_message}")
            return agent
            
        except Exception as e:
            logger.error(f"Error reporting agent error for {agent_id}: {e}")
            raise
    
    async def get_available_agents(
        self,
        task_type: Optional[str] = None,
        agent_type: Optional[AgentType] = None
    ) -> List[Agent]:
        """Get available agents that can accept tasks."""
        try:
            filters: Dict[str, Any] = {"status": AgentStatus.IDLE}
            
            if agent_type:
                filters["agent_type"] = agent_type.value
            
            agents = await self.get_all(filters=filters)
            
            # Filter by task type if provided
            if task_type:
                available_agents = []
                for agent in agents:
                    if agent.can_accept_task(task_type):
                        available_agents.append(agent)
                return available_agents
            
            return agents
            
        except Exception as e:
            logger.error(f"Error getting available agents: {e}")
            return []
    
    async def assign_task_to_agent(
        self,
        agent_id: ObjectId,
        task_id: ObjectId
    ) -> bool:
        """Assign a task to an agent."""
        agent = await self.get_by_id(agent_id)
        if not agent:
            raise NotFoundError(f"Agent {agent_id} not found")
        
        task = await Task.get(task_id)
        if not task:
            raise NotFoundError(f"Task {task_id} not found")
        
        try:
            # Check if agent can accept the task
            task_type = task.task_type
            if not task_type or not agent.can_accept_task(task_type):
                raise ValidationError(f"Agent {agent.name} cannot accept task of type {task_type}")
            
            # Assign task to agent
            task.agent_id = str(agent_id)
            task.agent_type = agent.agent_type.value
            await task.save()
            
            # Update agent workload
            await agent.increment_current_tasks()
            
            logger.info(f"Assigned task {task_id} to agent {agent.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error assigning task {task_id} to agent {agent_id}: {e}")
            raise
    
    async def complete_task_for_agent(
        self,
        agent_id: ObjectId,
        task_id: ObjectId,
        execution_time: float,
        success: bool
    ) -> Agent:
        """Complete a task for an agent and update metrics."""
        agent = await self.get_by_id(agent_id)
        if not agent:
            raise NotFoundError(f"Agent {agent_id} not found")
        
        try:
            # Update agent performance metrics
            await agent.update_performance_metrics(execution_time, success)
            
            # Update agent workload
            await agent.decrement_current_tasks()
            
            logger.info(f"Completed task {task_id} for agent {agent.name} (success: {success})")
            return agent
            
        except Exception as e:
            logger.error(f"Error completing task {task_id} for agent {agent_id}: {e}")
            raise
    
    async def get_agent_statistics(self, agent_id: ObjectId) -> Dict[str, Any]:
        """Get agent performance statistics."""
        agent = await self.get_by_id(agent_id)
        if not agent:
            raise NotFoundError(f"Agent {agent_id} not found")
        
        try:
            total_completed = agent.total_tasks_completed
            total_failed = agent.total_tasks_failed
            total_tasks = total_completed + total_failed
            
            stats = {
                "agent_id": str(agent.id),
                "name": agent.name,
                "agent_type": agent.agent_type,
                "status": agent.status,
                "total_tasks_completed": total_completed,
                "total_tasks_failed": total_failed,
                "total_tasks": total_tasks,
                "success_rate": agent.success_rate or 0.0,
                "average_execution_time": agent.average_execution_time_seconds or 0.0,
                "current_workload": agent.workload_percentage,
                "is_healthy": agent.is_healthy,
                "last_seen": agent.last_seen_at,
                "resource_usage": {
                    "cpu_percent": agent.cpu_usage_percent,
                    "memory_mb": agent.memory_usage_mb,
                    "disk_mb": agent.disk_usage_mb
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics for agent {agent_id}: {e}")
            return {}
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """Get system-wide agent statistics."""
        try:
            all_agents = await self.get_all()
            
            stats = {
                "total_agents": len(all_agents),
                "online_agents": 0,
                "idle_agents": 0,
                "busy_agents": 0,
                "error_agents": 0,
                "offline_agents": 0,
                "total_tasks_completed": 0,
                "total_tasks_failed": 0,
                "average_success_rate": 0.0,
                "agents_by_type": {}
            }
            
            success_rates = []
            
            for agent in all_agents:
                status = agent.status
                agent_type = agent.agent_type.value
                
                # Count by status
                if status == AgentStatus.IDLE:
                    stats["idle_agents"] += 1
                    stats["online_agents"] += 1
                elif status == AgentStatus.BUSY:
                    stats["busy_agents"] += 1
                    stats["online_agents"] += 1
                elif status == AgentStatus.ERROR:
                    stats["error_agents"] += 1
                elif status == AgentStatus.OFFLINE:
                    stats["offline_agents"] += 1
                
                # Count by type
                if agent_type not in stats["agents_by_type"]:
                    stats["agents_by_type"][agent_type] = 0
                stats["agents_by_type"][agent_type] += 1
                
                # Aggregate task counts
                stats["total_tasks_completed"] += agent.total_tasks_completed
                stats["total_tasks_failed"] += agent.total_tasks_failed
                
                # Collect success rates
                success_rate = agent.success_rate
                if success_rate is not None:
                    success_rates.append(success_rate)
            
            # Calculate average success rate
            if success_rates:
                stats["average_success_rate"] = sum(success_rates) / len(success_rates)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting system statistics: {e}")
            return {}
    
    async def cleanup_stale_agents(
        self,
        stale_hours: int = 24
    ) -> List[ObjectId]:
        """Clean up agents that haven't been seen for a long time."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=stale_hours)
            
            # Find stale agents
            stale_agents = []
            all_agents = await self.get_all()
            
            for agent in all_agents:
                last_seen = agent.last_seen_at
                if last_seen and last_seen < cutoff_time:
                    stale_agents.append(agent)
                elif not last_seen:
                    # Never seen, consider stale
                    created_at = agent.created_at
                    if created_at and created_at < cutoff_time:
                        stale_agents.append(agent)
            
            # Mark stale agents as offline
            stale_ids = []
            for agent in stale_agents:
                agent_id = agent.id
                await agent.mark_offline()
                stale_ids.append(agent_id)
            
            if stale_ids:
                logger.info(f"Marked {len(stale_ids)} stale agents as offline")
            
            return stale_ids
            
        except Exception as e:
            logger.error(f"Error cleaning up stale agents: {e}")
            return []


# Global agent service instance
agent_service = AgentService()