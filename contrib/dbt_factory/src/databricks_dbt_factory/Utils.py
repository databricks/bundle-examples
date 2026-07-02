def generate_task_key(dbt_node_full_name: str) -> str:
    """
    Generates a task key from a dbt node's fully qualified name by replacing dots with underscores.

    Args:
        dbt_node_full_name (str): Fully qualified dbt node name, e.g. `model.my_project.customers`.

    Returns:
        str: The generated task key (e.g. `model_my_project_customers`).
    """
    return dbt_node_full_name.replace(".", "_")
