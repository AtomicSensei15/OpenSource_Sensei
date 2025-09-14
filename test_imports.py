"""
Import test script for OpenSource Sensei agents
"""

import sys
from importlib import import_module

try:
    print("Importing Research Agent...")
    import_module('agents.research_agent')
    print('Research Agent module imported successfully')
    
    print("\nImporting QA Agent...")
    import_module('agents.qa_agent')
    print('QA Agent module imported successfully')
except Exception as e:
    print(f'Import error: {e}')