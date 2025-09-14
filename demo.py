"""
OpenSource Sensei Demo Entry Point

This script demonstrates the usage of the agent system, including:
- Research Agent
- Q&A Agent
"""

import asyncio
import logging
from agents import (
    AgentOrchestrator, 
    ResearchAgent, 
    QAAgent
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    """Main entry point to demonstrate agent functionality"""
    # Create and start the orchestrator
    orchestrator = AgentOrchestrator()
    await orchestrator.start()
    
    # Create and initialize agents
    research_agent = ResearchAgent()
    qa_agent = QAAgent()
    
    # Register agents with the orchestrator
    orchestrator.register_agent(research_agent)
    orchestrator.register_agent(qa_agent)
    
    # Initialize agents
    await research_agent.initialize()
    await qa_agent.initialize()
    
    # Display registered agents
    logger.info("Registered Agents:")
    agent_status = orchestrator.get_agent_status()
    for agent_id, status in agent_status.items():
        logger.info(f"  - {status['name']} ({agent_id}): {status['status']}")
        logger.info(f"    Capabilities: {', '.join(status['capabilities'])}")
    
    # Demonstrate Research Agent
    logger.info("\n=== Demonstrating Research Agent ===")
    research_task = {
        "type": "search_documentation",
        "query": "async/await patterns",
        "language": "python"
    }
    
    research_result = await research_agent.process_task(research_task)
    logger.info(f"Research Result: {research_result}")
    
    # Demonstrate Q&A Agent
    logger.info("\n=== Demonstrating Q&A Agent ===")
    qa_task = {
        "type": "answer_question",
        "question": "What are the best practices for error handling in Python?",
        "language": "python"
    }
    
    qa_result = await qa_agent.process_task(qa_task)
    logger.info(f"Q&A Result: {qa_result}")
    
    # Demonstrate agent collaboration
    logger.info("\n=== Demonstrating Agent Collaboration ===")
    # Research agent collaborates with Q&A agent
    collaboration_result = await research_agent.collaborate_with_agent(
        "qa_agent",
        {
            "type": "explain_code",
            "code": "async def example():\n    result = await some_coroutine()\n    return result",
            "language": "python"
        }
    )
    logger.info(f"Collaboration Result: {collaboration_result}")
    
    # Define a workflow
    orchestrator.define_workflow(
        "research_and_explain",
        {
            "steps": [
                {
                    "name": "find_examples",
                    "agent_id": "research_agent",
                    "task": {
                        "type": "find_code_examples",
                        "query": "async context manager",
                        "language": "python"
                    }
                },
                {
                    "name": "explain_example",
                    "agent_id": "qa_agent",
                    "task": {
                        "type": "explain_code",
                        "code": "${find_examples.examples[0].code}",
                        "language": "python"
                    }
                }
            ]
        }
    )
    
    # Execute workflow
    logger.info("\n=== Executing Workflow ===")
    try:
        workflow_result = await orchestrator.execute_workflow(
            "research_and_explain", {}
        )
        logger.info(f"Workflow Result: {workflow_result}")
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
    
    # Shutdown agents and orchestrator
    await orchestrator.stop()
    logger.info("Demo completed")

if __name__ == "__main__":
    asyncio.run(main())