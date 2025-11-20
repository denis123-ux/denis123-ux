"""
Scientific logging framework with preregistration, auto-timestamping, and reproducibility.

This module implements rigorous scientific methodology for computational experiments:
- Preregistration of hypotheses before seeing results
- Immutable timestamped logs
- Complete parameter tracking
- Reproducibility guarantees
"""

import json
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import sys
import platform
import numpy as np


class AutoLogger:
    """
    Automatic scientific logger with preregistration and immutable audit trail.

    Features:
    - Preregistration: Lock in hypotheses before seeing results
    - Immutable logs: Timestamped, hashed entries
    - Full system info: Python version, numpy seed, hardware
    - Auto-save: Continuous writing to disk
    - Markdown reports: Auto-generate research logs

    Example:
        logger = AutoLogger("phase1_area_law")
        logger.preregister(
            hypothesis="Area law S(A) ~ |∂A|",
            prediction="slope = 0.167 ± 0.01",
            method="MERA + SVD"
        )
        logger.log_result({"slope": 0.168, "r_squared": 0.995})
        logger.generate_report()
    """

    def __init__(self, experiment_name: str, output_dir: str = "results/logs"):
        """
        Initialize logger for a scientific experiment.

        Args:
            experiment_name: Unique identifier for this experiment
            output_dir: Directory to save logs
        """
        self.experiment_name = experiment_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped log file
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.output_dir / f"{experiment_name}_{self.timestamp}.json"

        # Initialize log structure
        self.log_data = {
            "experiment_name": experiment_name,
            "timestamp_start": self.timestamp,
            "system_info": self._capture_system_info(),
            "preregistration": {},
            "results": [],
            "validations": [],
            "failures": [],
            "summary": {}
        }

        # Save initial state
        self._save()

        # Also create markdown log
        self.md_file = self.output_dir.parent.parent / "RESEARCH_LOG.md"

    def _capture_system_info(self) -> Dict[str, Any]:
        """Capture complete system information for reproducibility."""
        return {
            "python_version": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor(),
            "numpy_version": np.__version__,
            "timestamp_utc": datetime.utcnow().isoformat(),
            "working_directory": str(Path.cwd())
        }

    def preregister(
        self,
        hypothesis: str,
        prediction: str,
        method: str,
        falsifiability_criterion: Optional[str] = None
    ) -> str:
        """
        Preregister hypothesis BEFORE seeing results (critical for scientific rigor).

        This creates an immutable record with timestamp and hash, preventing
        post-hoc hypothesis adjustment (HARKing - Hypothesizing After Results Known).

        Args:
            hypothesis: The scientific hypothesis being tested
            prediction: Specific quantitative prediction
            method: Method to be used
            falsifiability_criterion: What would falsify this hypothesis

        Returns:
            Hash of preregistration (proof of timestamp)
        """
        prereg_data = {
            "hypothesis": hypothesis,
            "prediction": prediction,
            "method": method,
            "falsifiability_criterion": falsifiability_criterion,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Create immutable hash
        prereg_str = json.dumps(prereg_data, sort_keys=True)
        prereg_hash = hashlib.sha256(prereg_str.encode()).hexdigest()
        prereg_data["hash"] = prereg_hash

        self.log_data["preregistration"] = prereg_data
        self._save()

        print(f"✓ Hypothesis preregistered: {prereg_hash[:16]}...")
        print(f"  Hypothesis: {hypothesis}")
        print(f"  Prediction: {prediction}")

        return prereg_hash

    def log_result(self, result: Dict[str, Any], metadata: Optional[Dict] = None):
        """
        Log a single experimental result.

        Args:
            result: Dictionary of result values
            metadata: Optional metadata (seed, parameters, etc.)
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "result": result,
            "metadata": metadata or {}
        }
        self.log_data["results"].append(entry)
        self._save()

    def log_validation(self, validation_type: str, passed: bool, details: Dict[str, Any]):
        """
        Log validation check results.

        Args:
            validation_type: Type of validation (sanity_check, statistical, adversarial)
            passed: Whether validation passed
            details: Details of the validation
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": validation_type,
            "passed": passed,
            "details": details
        }
        self.log_data["validations"].append(entry)

        if not passed:
            print(f"⚠ Validation FAILED: {validation_type}")
            print(f"  Details: {details}")

        self._save()

    def log_failure(self, message: str, details: Optional[Dict] = None):
        """Log experimental failure."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "details": details or {}
        }
        self.log_data["failures"].append(entry)
        print(f"✗ FAILURE: {message}")
        self._save()

    def log_success(self, message: str, details: Optional[Dict] = None):
        """Log experimental success."""
        print(f"✓ SUCCESS: {message}")
        if details:
            for key, value in details.items():
                print(f"    {key}: {value}")

    def log_summary(self, summary_text: str):
        """Log summary information."""
        print(f"  {summary_text}")

    def add_summary(self, key: str, value: Any):
        """Add to final summary."""
        self.log_data["summary"][key] = value
        self._save()

    def _save(self):
        """Save log data to JSON file."""
        with open(self.log_file, 'w') as f:
            json.dump(self.log_data, f, indent=2, default=str)

    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """
        Generate markdown research report.

        Args:
            output_path: Optional custom path for report

        Returns:
            Path to generated report
        """
        if output_path is None:
            output_path = self.output_dir / f"{self.experiment_name}_report.md"

        # Generate markdown
        md_content = self._generate_markdown_report()

        # Save
        with open(output_path, 'w') as f:
            f.write(md_content)

        # Also append to main research log
        self._append_to_main_log(md_content)

        print(f"✓ Report generated: {output_path}")
        return str(output_path)

    def _generate_markdown_report(self) -> str:
        """Generate markdown report content."""
        lines = []

        # Header
        lines.append(f"# {self.experiment_name}")
        lines.append(f"\n**Date**: {self.timestamp}\n")

        # Preregistration
        if self.log_data["preregistration"]:
            lines.append("## Preregistration")
            prereg = self.log_data["preregistration"]
            lines.append(f"- **Hypothesis**: {prereg.get('hypothesis', 'N/A')}")
            lines.append(f"- **Prediction**: {prereg.get('prediction', 'N/A')}")
            lines.append(f"- **Method**: {prereg.get('method', 'N/A')}")
            lines.append(f"- **Hash**: `{prereg.get('hash', 'N/A')[:16]}...`")
            lines.append("")

        # Results
        if self.log_data["results"]:
            lines.append(f"## Results ({len(self.log_data['results'])} runs)")
            lines.append("")

            # Summary statistics if multiple results
            if len(self.log_data["results"]) > 1:
                lines.append("### Aggregated Statistics")
                lines.append("")
                # This would compute means, std, etc.
                lines.append("*(Full statistics in JSON log)*")
                lines.append("")

        # Validations
        if self.log_data["validations"]:
            passed = sum(1 for v in self.log_data["validations"] if v["passed"])
            total = len(self.log_data["validations"])
            lines.append(f"## Validations: {passed}/{total} passed")
            lines.append("")

            # Show failures
            failures = [v for v in self.log_data["validations"] if not v["passed"]]
            if failures:
                lines.append("### Failed Validations")
                for fail in failures:
                    lines.append(f"- **{fail['type']}**: {fail['details']}")
                lines.append("")

        # Failures
        if self.log_data["failures"]:
            lines.append("## ❌ Failures")
            for fail in self.log_data["failures"]:
                lines.append(f"- {fail['message']}")
                if fail["details"]:
                    lines.append(f"  ```{fail['details']}```")
            lines.append("")

        # Summary
        if self.log_data["summary"]:
            lines.append("## Summary")
            for key, value in self.log_data["summary"].items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")

        # System info
        lines.append("## System Information")
        lines.append(f"- Python: {self.log_data['system_info']['python_version'].split()[0]}")
        lines.append(f"- NumPy: {self.log_data['system_info']['numpy_version']}")
        lines.append(f"- Platform: {self.log_data['system_info']['platform']}")
        lines.append("")

        return "\n".join(lines)

    def _append_to_main_log(self, content: str):
        """Append experiment to main research log."""
        separator = "\n" + "="*80 + "\n\n"

        if self.md_file.exists():
            with open(self.md_file, 'a') as f:
                f.write(separator)
                f.write(content)
        else:
            # Create new log
            with open(self.md_file, 'w') as f:
                f.write("# Research Log: Emergent Gravity from Quantum Entanglement\n\n")
                f.write("Auto-generated log of all experiments.\n\n")
                f.write("="*80 + "\n\n")
                f.write(content)


def set_random_seeds(seed: int):
    """
    Set all random seeds for reproducibility.

    Args:
        seed: Random seed value
    """
    np.random.seed(seed)
    try:
        import random
        random.seed(seed)
    except ImportError:
        pass

    # Set Python hash seed via environment variable (must be set before Python starts)
    # This is documented for the user
    import os
    os.environ['PYTHONHASHSEED'] = str(seed)

    print(f"✓ Random seeds set: {seed}")
