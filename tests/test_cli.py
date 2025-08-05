"""Tests for the MigrateX CLI interface."""

import pytest
from pathlib import Path
from typer.testing import CliRunner

from migratex.main import app


class TestCLI:
    def setup_method(self):
        self.runner = CliRunner()

    def test_cli_accepts_repository_path(self):
        """Test that CLI accepts a repository path argument."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "repository-path" in result.stdout or "source" in result.stdout

    def test_cli_accepts_target_language(self):
        """Test that CLI accepts a target language argument."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "target" in result.stdout or "language" in result.stdout

    def test_cli_rejects_invalid_path(self):
        """Test that CLI rejects non-existent repository paths."""
        result = self.runner.invoke(app, ["translate", "/non/existent/path", "rust"])
        assert result.exit_code != 0

    def test_cli_rejects_invalid_language(self):
        """Test that CLI rejects unsupported target languages."""
        result = self.runner.invoke(app, ["translate", ".", "cobol"])
        assert result.exit_code != 0

    @pytest.mark.integration
    def test_cli_processes_simple_repository(self, tmp_path):
        """Test that CLI can process a simple C repository."""
        # Create a simple C file
        c_file = tmp_path / "hello.c"
        c_file.write_text("""
#include <stdio.h>

int main() {
    printf("Hello, World!\\n");
    return 0;
}
""")
        
        result = self.runner.invoke(app, ["translate", str(tmp_path), "rust", "--dry-run"])
        assert result.exit_code == 0