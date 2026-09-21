import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'ml')
import pytest
sys.exit(pytest.main(['-q', 'backend/tests']))