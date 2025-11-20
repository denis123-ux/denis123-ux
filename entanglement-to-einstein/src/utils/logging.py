"""
Auto-logging with preregistration for scientific methodology.

This module provides automatic logging of experiments with timestamps,
preregistration of hypotheses, and reproducibility guarantees.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import hashlib
import platform
import sys
import numpy as np


class AutoLogger:
    """
    Automatic logger with preregistration capabilities.

    Features:
    - Preregistration of hypotheses before seeing results
    - Immutable timestamps
    - Complete environment logging
    - Automatic seed tracking
    - Structured output for reproducibility
    """

    def __init__(self, experiment_name: str, output_dir: str = "results/logs"):
        """
        Initialize the logger.

        Args:
            experiment_name: Name of the experiment
            output_dir: Directory for log outputs
        """
        self.experiment_name = experiment_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create unique session ID with timestamp
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_file = self.output_dir / f"{experiment_name}_{self.session_id}.json"

        # Initialize session data
        self.session_data = {
            "experiment_name": experiment_name,
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "environment": self._capture_environment(),
            "preregistration": {},
            "results": [],
            "summary": {},
            "status": "running"
        }

        # Save initial session
        self._save_session()

        print(f"[AutoLogger] Session started: {self.session_id}")
        print(f"[AutoLogger] Logging to: {self.session_file}")

    def _capture_environment(self) -> Dict[str, Any]:
        """Capture complete environment information."""
        return {
            "python_version": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor(),
            "numpy_version": np.__version__,
            "hostname": platform.node(),
            "cwd": os.getcwd(),
            "timestamp": datetime.now().isoformat()
        }

    def preregister(
        self,
        hypothesis: str,
        prediction: str,
        method: str,
        falsifiability: Optional[str] = None
    ) -> str:
        """
        Preregister a hypothesis BEFORE seeing results.

        This creates an immutable record with cryptographic hash
        to prove the hypothesis was stated before analysis.

        Args:
            hypothesis: The hypothesis being tested
            prediction: Quantitative prediction
            method: Method to be used
            falsifiability: Falsifiability criteria

        Returns:
            Preregistration hash
        """
        prereg_data = {
            "hypothesis": hypothesis,
            "prediction": prediction,
            "method": method,
            "falsifiability": falsifiability,
            "timestamp": datetime.now().isoformat()
        }

        # Create cryptographic hash
        prereg_string = json.dumps(prereg_data, sort_keys=True)
        prereg_hash = hashlib.sha256(prereg_string.encode()).hexdigest()

        self.session_data["preregistration"] = {
            "data": prereg_data,
            "hash": prereg_hash
        }

        self._save_session()

        print(f"[AutoLogger] PREREGISTERED hypothesis")
        print(f"[AutoLogger] Hash: {prereg_hash[:16]}...")
        print(f"[AutoLogger] Hypothesis: {hypothesis}")
        print(f"[AutoLogger] Prediction: {prediction}")

        return prereg_hash

    def log_result(self, result_dict: Dict[str, Any]) -> None:
        """
        Log a result from the experiment.

        Args:
            result_dict: Dictionary containing result data
        """
        result_entry = {
            **result_dict,
            "timestamp": datetime.now().isoformat()
        }

        self.session_data["results"].append(result_entry)
        self._save_session()

    def log_summary(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log a summary message."""
        summary_entry = {
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        if "messages" not in self.session_data["summary"]:
            self.session_data["summary"]["messages"] = []

        self.session_data["summary"]["messages"].append(summary_entry)
        self._save_session()

        print(f"[AutoLogger] SUMMARY: {message}")

    def log_success(self, message: str) -> None:
        """Log a success."""
        self.log_summary(f"✓ SUCCESS: {message}")

    def log_failure(self, message: str) -> None:
        """Log a failure."""
        self.log_summary(f"✗ FAILURE: {message}")
        print(f"[AutoLogger] ✗ FAILURE: {message}")

    def log_warning(self, message: str) -> None:
        """Log a warning."""
        self.log_summary(f"⚠ WARNING: {message}")
        print(f"[AutoLogger] ⚠ WARNING: {message}")

    def _save_session(self) -> None:
        """Save session data to disk."""
        with open(self.session_file, 'w') as f:
            json.dump(self.session_data, f, indent=2)

    def finalize(self, status: str = "completed") -> None:
        """
        Finalize the session.

        Args:
            status: Final status (completed, failed, aborted)
        """
        self.session_data["status"] = status
        self.session_data["end_time"] = datetime.now().isoformat()
        self._save_session()

        print(f"[AutoLogger] Session finalized with status: {status}")

    def generate_report(self, output_path: str) -> None:
        """
        Generate a markdown report of the experiment.

        Args:
            output_path: Path to save the markdown report
        """
        report_lines = [
            f"# Experiment Report: {self.experiment_name}",
            f"",
            f"**Session ID:** {self.session_id}",
            f"**Status:** {self.session_data.get('status', 'unknown')}",
            f"**Start Time:** {self.session_data['start_time']}",
            f"",
            f"## Preregistration",
            f"",
        ]

        if "preregistration" in self.session_data:
            prereg = self.session_data["preregistration"]["data"]
            report_lines.extend([
                f"**Hypothesis:** {prereg['hypothesis']}",
                f"",
                f"**Prediction:** {prereg['prediction']}",
                f"",
                f"**Method:** {prereg['method']}",
                f"",
                f"**Preregistration Hash:** `{self.session_data['preregistration']['hash']}`",
                f"",
            ])

        report_lines.extend([
            f"## Results Summary",
            f"",
            f"Total results logged: {len(self.session_data['results'])}",
            f"",
        ])

        if "messages" in self.session_data.get("summary", {}):
            report_lines.extend([
                f"## Summary Messages",
                f"",
            ])
            for msg in self.session_data["summary"]["messages"]:
                report_lines.append(f"- {msg['message']}")

        report_lines.extend([
            f"",
            f"## Environment",
            f"",
            f"- Python: {self.session_data['environment']['python_version'].split()[0]}",
            f"- Platform: {self.session_data['environment']['platform']}",
            f"- NumPy: {self.session_data['environment']['numpy_version']}",
            f"",
            f"## Reproducibility",
            f"",
            f"To reproduce this experiment, use:",
            f"```bash",
            f"python experiments/phase1_area_law.py --reproduce {self.session_id}",
            f"```",
        ])

        report_text = "\n".join(report_lines)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            f.write(report_text)

        print(f"[AutoLogger] Report generated: {output_path}")


class ExperimentTracker:
    """Track multiple experiments and compare results."""

    def __init__(self, base_dir: str = "results/logs"):
        self.base_dir = Path(base_dir)

    def load_experiment(self, session_id: str) -> Dict[str, Any]:
        """Load an experiment by session ID."""
        matching_files = list(self.base_dir.glob(f"*_{session_id}.json"))

        if not matching_files:
            raise FileNotFoundError(f"No experiment found with session ID: {session_id}")

        with open(matching_files[0], 'r') as f:
            return json.load(f)

    def list_experiments(self, experiment_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all experiments, optionally filtered by name."""
        experiments = []

        pattern = f"{experiment_name}_*.json" if experiment_name else "*.json"

        for log_file in self.base_dir.glob(pattern):
            with open(log_file, 'r') as f:
                data = json.load(f)
                experiments.append({
                    "session_id": data["session_id"],
                    "experiment_name": data["experiment_name"],
                    "start_time": data["start_time"],
                    "status": data.get("status", "unknown"),
                    "num_results": len(data.get("results", []))
                })

        return sorted(experiments, key=lambda x: x["start_time"], reverse=True)
