import json
from pathlib import Path

import pytest
from external_resources_io.config import EnvVar

from er_aws_rds_proxy.__main__ import get_ai_input  # noqa: PLC2701
from er_aws_rds_proxy.app_interface_input import AppInterfaceInput
from tests.conftest import build_input_data


@pytest.fixture(autouse=True)
def prepare_test_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Prepare the test environment."""
    input_json = tmp_path / "input.json"
    input_json.write_text(json.dumps(build_input_data()))
    monkeypatch.setenv(EnvVar.INPUT_FILE, str(input_json.absolute()))


def test_get_ai_input(ai_input: AppInterfaceInput) -> None:
    """Test get_ai_input."""
    main_ai_input = get_ai_input()
    assert isinstance(main_ai_input, AppInterfaceInput)
    assert main_ai_input == ai_input
