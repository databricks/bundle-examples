from os import path

import my_custom_library
import my_custom_library.parameters


def mock_bundle_file_path(monkeypatch):
    def mock():
        return path.join(path.dirname(__file__), "..")

    monkeypatch.setattr(
        my_custom_library.parameters,
        "bundle_file_path",
        mock,
    )


def mock_bundle_target(monkeypatch):
    def mock():
        return "test"

    monkeypatch.setattr(
        my_custom_library.parameters,
        "bundle_target",
        mock,
    )


def test_load_configuration(monkeypatch):
    mock_bundle_file_path(monkeypatch)
    mock_bundle_target(monkeypatch)

    configuration = my_custom_library.load_configuration()
    assert configuration == ["this is my test config"]
