import json


class SpecsHandler:
    """Reads dbt manifests for the factory."""

    @staticmethod
    def read_dbt_manifest(path: str) -> dict:
        """
        Reads a dbt manifest JSON file and returns its parsed content.

        Args:
            path (str): Path to the manifest file.

        Returns:
            dict: Parsed manifest content.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not valid JSON.
        """
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Manifest file not found: {path}. Details: {e}") from e
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing JSON from manifest file: {path}. Details: {e}") from e
