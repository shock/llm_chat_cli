import pytest

@pytest.fixture(autouse=True)
def print_test_name(request):
    print(f"Running test: {request.node.name}")