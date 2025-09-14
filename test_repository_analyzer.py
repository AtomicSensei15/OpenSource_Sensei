import os
import tempfile
import asyncio
import json
from agents.repository_analyzer import RepositoryAnalysisAgent

async def run_analysis(path: str):
    agent = RepositoryAnalysisAgent()
    return await agent._analyze_local_repository(path)

def test_project_type_detection_node_and_python():
    tmp = tempfile.mkdtemp(prefix="sensei_test_")
    try:
        # Node.js sentinel
        with open(os.path.join(tmp, 'package.json'), 'w', encoding='utf-8') as f:
            f.write('{"name": "test-project", "version": "1.0.0"}')
        # Simple JS file
        with open(os.path.join(tmp, 'index.js'), 'w', encoding='utf-8') as f:
            f.write('console.log("hello");')

        result = asyncio.run(run_analysis(tmp))
        assert result['metadata']['project_type'] == 'Node.js'
        assert 'total_lines' in result['languages']

        # Switch to Python project
        os.remove(os.path.join(tmp, 'package.json'))
        with open(os.path.join(tmp, 'requirements.txt'), 'w', encoding='utf-8') as f:
            f.write('flask==2.0.1\npytest==6.2.5\n')
        with open(os.path.join(tmp, 'app.py'), 'w', encoding='utf-8') as f:
            f.write('print("hi")\n')

        result2 = asyncio.run(run_analysis(tmp))
        assert result2['metadata']['project_type'] == 'Python'
    finally:
        # Leave temp dir for debugging if needed (could clean with shutil.rmtree)
        pass

if __name__ == '__main__':
    # Simple manual run
    test_project_type_detection_node_and_python()
    print('Tests passed')
