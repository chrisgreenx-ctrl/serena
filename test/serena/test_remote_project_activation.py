
import os
import shutil
import tempfile
import pytest
from pathlib import Path
from serena.agent import SerenaAgent, ProjectNotFoundError
from serena.config.serena_config import SerenaConfig

def test_activate_non_existent_project_creates_it():
    # Setup: Ensure the directory does NOT exist
    # Use a safe temp directory path
    temp_dir = tempfile.mkdtemp()
    non_existent_project_path = os.path.join(temp_dir, "new_project")

    # Ensure it doesn't exist
    if os.path.exists(non_existent_project_path):
        shutil.rmtree(non_existent_project_path)

    try:
        # Create a temporary config file for Serena
        with tempfile.NamedTemporaryFile(suffix=".yml", delete=False, mode='w') as tmp_config:
            tmp_config.write("projects: []\n")
            tmp_config_path = tmp_config.name

        try:
            config = SerenaConfig(
                config_file_path=tmp_config_path,
                projects=[],
                loaded_commented_yaml={"projects": []}
            )

            agent = SerenaAgent(serena_config=config)

            # Action: Activate the non-existent project
            project = agent.activate_project_from_path_or_name(non_existent_project_path)

            # Assertions
            assert os.path.isdir(non_existent_project_path), "Project directory should have been created"
            assert project is not None, "Project instance should be returned"
            assert project.project_root == str(Path(non_existent_project_path).resolve()), "Project root path should match"
            assert os.path.exists(os.path.join(non_existent_project_path, ".serena", "project.yml")), "project.yml should exist"

            # Check if languages is empty list
            assert project.project_config.languages == [], "New empty project should have no languages by default"

        finally:
            if os.path.exists(tmp_config_path):
                os.remove(tmp_config_path)

    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
