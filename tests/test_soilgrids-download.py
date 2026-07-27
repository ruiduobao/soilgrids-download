#!/usr/bin/env python3
"""
Tests for soilgrids-download CLI.
Run with: python -m pytest tests/ -v
"""

import sys
import os
import json
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

try:
    import soilgrids_download as sgd
except ImportError:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "soilgrids_download",
        str(Path(__file__).parent.parent / "scripts" / "soilgrids_download.py"),
    )
    sgd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sgd)


class TestValidation(unittest.TestCase):
    """Test input validation functions."""

    def test_validate_latlon_valid(self):
        """Test valid lat/lon values."""
        sgd.validate_latlon(39.9042, 116.4074)
        sgd.validate_latlon(-90, -180)
        sgd.validate_latlon(90, 180)

    def test_validate_latlon_invalid(self):
        """Test invalid lat/lon values."""
        with self.assertRaises(ValueError):
            sgd.validate_latlon(91, 0)
        with self.assertRaises(ValueError):
            sgd.validate_latlon(0, 181)

    def test_validate_bbox_valid(self):
        """Test valid bounding box."""
        result = sgd.validate_bbox([73, 18, 135, 54])
        self.assertEqual(result, (73, 18, 135, 54))

    def test_validate_bbox_invalid(self):
        """Test invalid bounding box."""
        with self.assertRaises(ValueError):
            sgd.validate_bbox([73, 54, 135, 18])

    def test_validate_depths_valid(self):
        """Test valid depth layers."""
        result = sgd.validate_depths(["0-5cm", "5-15cm"])
        self.assertEqual(result, ["0-5cm", "5-15cm"])

    def test_validate_depths_invalid(self):
        """Test invalid depth layer."""
        with self.assertRaises(ValueError):
            sgd.validate_depths(["0-5cm", "invalid-depth"])


class TestOutput(unittest.TestCase):
    """Test output writing functions."""

    def test_write_csv(self):
        """Test CSV output."""
        records = [
            {"latitude": 39.9, "longitude": 116.4, "property": "phh2o", "depth": "0-5cm", "mean": 72},
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name
        try:
            sgd.write_csv(records, output_path)
            with open(output_path, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["property"], "phh2o")
        finally:
            os.unlink(output_path)

    def test_write_json(self):
        """Test JSON output."""
        records = [
            {"latitude": 39.9, "longitude": 116.4, "property": "phh2o", "mean": 72},
        ]
        metadata = {"source": "ISRIC SoilGrids v2.0"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name
        try:
            sgd.write_json(records, output_path, metadata)
            with open(output_path, "r") as f:
                data = json.load(f)
            self.assertEqual(data["count"], 1)
            self.assertEqual(data["metadata"]["source"], "ISRIC SoilGrids v2.0")
        finally:
            os.unlink(output_path)


class TestParseResponse(unittest.TestCase):
    """Test API response parsing."""

    def test_parse_point_response(self):
        """Test parsing point query response."""
        mock_data = {
            "properties": {
                "layers": [
                    {
                        "name": "phh2o",
                        "unit_measure": {"mapped_units": "pH x10"},
                        "depths": [
                            {
                                "label": "0-5cm",
                                "values": {"mean": 72, "Q0.05": 65, "Q0.5": 72, "Q0.95": 79},
                            }
                        ],
                    }
                ]
            }
        }
        records = sgd.parse_point_response(mock_data, ["phh2o"], 39.9, 116.4)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["property"], "phh2o")
        self.assertEqual(records[0]["mean"], 72)

    def test_parse_empty_response(self):
        """Test parsing empty response."""
        mock_data = {"properties": {"layers": []}}
        records = sgd.parse_point_response(mock_data, ["phh2o"], 39.9, 116.4)
        self.assertEqual(len(records), 0)


class TestCLI(unittest.TestCase):
    """Test CLI argument parsing."""

    def test_help_message(self):
        """Test that help message can be displayed."""
        with self.assertRaises(SystemExit) as cm:
            with patch("sys.argv", ["soilgrids-download", "--help"]):
                sgd.main()
        self.assertEqual(cm.exception.code, 0)

    def test_list_properties_command(self):
        """Test list-properties command."""
        with patch("sys.argv", ["soilgrids-download", "list-properties"]):
            sgd.main()

    def test_list_depths_command(self):
        """Test list-depths command."""
        with patch("sys.argv", ["soilgrids-download", "list-depths"]):
            sgd.main()

    def test_query_subcommand_help_shows_verbose(self):
        """`query --help` should mention the new --verbose / -v flag."""
        import subprocess
        script = str(Path(__file__).parent.parent / "scripts" / "soilgrids_download.py")
        result = subprocess.run(
            [sys.executable, script, "query", "--help"],
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--verbose", result.stdout)
        self.assertIn("-v", result.stdout)


class TestVerbose(unittest.TestCase):
    """Tests for --verbose flag on the query subcommand."""

    def _fake_response(self):
        return {
            "properties": {
                "layers": [
                    {
                        "name": "phh2o",
                        "unit_measure": {"mapped_units": "pH x10"},
                        "depths": [
                            {
                                "label": "0-5cm",
                                "values": {"mean": 72, "Q0.05": 65, "Q0.5": 72, "Q0.95": 79},
                            }
                        ],
                    }
                ]
            }
        }

    @patch("soilgrids_download.fetch_soilgrids_point")
    def test_verbose_off_by_default(self, mock_fetch):
        """Without --verbose, no [verbose] log lines should be emitted to stderr."""
        import io
        from contextlib import redirect_stderr
        mock_fetch.return_value = self._fake_response()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            out_path = f.name
        try:
            args = sgd.argparse.Namespace(
                preset=None, property="phh2o",
                place=None, lat=39.9, lon=116.4, bbox=None,
                depth=None, output=out_path, format="csv",
                qa=False, verbose=False,
            )
            err = io.StringIO()
            with redirect_stderr(err):
                sgd.cmd_query(args)
            out = err.getvalue()
            self.assertNotIn("[verbose]", out)
        finally:
            os.unlink(out_path)

    @patch("soilgrids_download.fetch_soilgrids_point")
    def test_verbose_emits_logs(self, mock_fetch):
        """With --verbose=True, [verbose] log lines should appear on stderr."""
        import io
        from contextlib import redirect_stderr
        mock_fetch.return_value = self._fake_response()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            out_path = f.name
        try:
            args = sgd.argparse.Namespace(
                preset=None, property="phh2o",
                place=None, lat=39.9, lon=116.4, bbox=None,
                depth=None, output=out_path, format="csv",
                qa=False, verbose=True,
            )
            err = io.StringIO()
            with redirect_stderr(err):
                sgd.cmd_query(args)
            out = err.getvalue()
            self.assertIn("[verbose]", out)
            self.assertIn("resolved:", out)
            self.assertIn("parsed 1 record", out)
            self.assertIn("wrote 1 record", out)
        finally:
            os.unlink(out_path)

    @patch("soilgrids_download.fetch_soilgrids_point")
    def test_verbose_short_flag(self, mock_fetch):
        """The short -v flag should also enable verbose mode."""
        import io
        from contextlib import redirect_stderr
        mock_fetch.return_value = self._fake_response()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            out_path = f.name
        try:
            args = sgd.argparse.Namespace(
                preset=None, property="phh2o",
                place=None, lat=39.9, lon=116.4, bbox=None,
                depth=None, output=out_path, format="csv",
                qa=False, verbose=True,
            )
            err = io.StringIO()
            with redirect_stderr(err):
                sgd.cmd_query(args)
            out = err.getvalue()
            self.assertIn("[verbose]", out)
        finally:
            os.unlink(out_path)


if __name__ == "__main__":
    unittest.main()
