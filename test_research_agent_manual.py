import asyncio
from agents.research_agent import ResearchAgent

async def main():
    agent = ResearchAgent()
    await agent.initialize()
    task_new = {"type": "research_best_practices", "topic": "error handling", "language": "python"}
    task_legacy = {"task_type": "research_best_practices", "topic": "testing", "language": "python"}
    res_new = await agent.process_task(task_new)
    res_legacy = await agent.process_task(task_legacy)
    print('NEW KEY OK:', list(res_new.keys()))
    print('LEGACY KEY OK:', list(res_legacy.keys()))

if __name__ == '__main__':
    asyncio.run(main())
