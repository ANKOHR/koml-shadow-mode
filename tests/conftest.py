import pytest
from koml_shadow_mode.fixtures import generate

@pytest.fixture
def fixture_dir(tmp_path):
    generate(tmp_path)
    return tmp_path
