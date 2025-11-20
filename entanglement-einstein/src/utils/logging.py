"""
Auto-Logging System with Preregistration for Scientific Rigor
==============================================================

Implements immutable preregistration of hypotheses, automatic logging
of all experimental parameters, and timestamped result tracking.
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import sys
import platform
import numpy as np


class AutoLogger:
    """
    Automatic logger with preregistration for scientific reproducibility.

    Features:
    - Immutable hypothesis preregistration (SHA-256 hash)
    - Automatic timestamping
    - System info capture
    - Structured JSON output
    - Markdown report generation

    Parameters
    ----------
    experiment_name : str
        Name of the experiment
    output_dir : str or Path, optional
        Directory for logs (default: results/logs)
    """

    def __init__(
        self,
        experiment_name: str,
        output_dir: Optional[Path] = None
    ):
        self.experiment_name = experiment_name
        self.output_dir = Path(output_dir) if output_dir else Path("results/logs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique timestamp
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_id = f"{experiment_name}_{self.timestamp}"

        # Initialize storage
        self.preregistration: Dict[str, Any] = {}
        self.results: List[Dict[str, Any]] = []
        self.summary: List[str] = []
        self.failures: List[str] = []
        self.successes: List[str] = []

        # Capture system info
        self.system_info = self._capture_system_info()

        # Create log files
        self.log_file = self.output_dir / f"{self.session_id}.json"
        self.report_file = self.output_dir / f"{self.session_id}_report.md"

        print(f"📊 AutoLogger initialized: {self.session_id}")
        print(f"📁 Output: {self.output_dir}")

    def _capture_system_info(self) -> Dict[str, Any]:
        """Capture system information for reproducibility."""
        return {
            'timestamp': self.timestamp,
            'python_version': sys.version,
            'platform': platform.platform(),
            'processor': platform.processor(),
            'numpy_version': np.__version__,
            'numpy_config': {
                'BLAS': np.__config__.blas_opt_info if hasattr(np.__config__, 'blas_opt_info') else None
            }
        }

    def preregister(
        self,
        hypothesis: str,
        prediction: str,
        method: str,
        falsifiability: Optional[str] = None
    ) -> str:
        """
        Preregister hypothesis with immutable hash BEFORE seeing results.

        Parameters
        ----------
        hypothesis : str
            The hypothesis being tested
        prediction : str
            Quantitative prediction
        method : str
            Experimental method
        falsifiability : str, optional
            How to falsify the hypothesis

        Returns
        -------
        str
            SHA-256 hash of preregistration (proof of timestamp)
        """
        # Create preregistration record
        prereg = {
            'hypothesis': hypothesis,
            'prediction': prediction,
            'method': method,
            'falsifiability': falsifiability,
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id
        }

        # Create immutable hash
        prereg_str = json.dumps(prereg, sort_keys=True)
        prereg_hash = hashlib.sha256(prereg_str.encode()).hexdigest()
        prereg['hash'] = prereg_hash

        self.preregistration = prereg

        # Save immediately (immutable record)
        prereg_file = self.output_dir / f"{self.session_id}_PREREGISTRATION.json"
        with open(prereg_file, 'w') as f:
            json.dump(prereg, f, indent=2)

        print(f"\n{'='*60}")
        print(f"✓ HYPOTHESIS PREREGISTERED (IMMUTABLE)")
        print(f"{'='*60}")
        print(f"Hypothesis: {hypothesis}")
        print(f"Prediction: {prediction}")
        print(f"Method: {method}")
        if falsifiability:
            print(f"Falsifiability: {falsifiability}")
        print(f"Hash: {prereg_hash[:16]}...")
        print(f"Timestamp: {prereg['timestamp']}")
        print(f"{'='*60}\n")

        return prereg_hash

    def log_result(self, result: Dict[str, Any]) -> None:
        """Log a single experimental result."""
        result['_logged_at'] = datetime.now().isoformat()
        self.results.append(result)

        # Save incrementally
        self._save_incremental()

    def log_summary(self, message: str) -> None:
        """Log a summary message."""
        self.summary.append({
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        print(f"📝 {message}")

    def log_failure(self, message: str) -> None:
        """Log a failure."""
        self.failures.append({
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        print(f"❌ FAILURE: {message}")

    def log_success(self, message: str) -> None:
        """Log a success."""
        self.successes.append({
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        print(f"✓ SUCCESS: {message}")

    def _save_incremental(self) -> None:
        """Save current state incrementally."""
        data = {
            'experiment': self.experiment_name,
            'session_id': self.session_id,
            'system_info': self.system_info,
            'preregistration': self.preregistration,
            'results': self.results,
            'summary': self.summary,
            'failures': self.failures,
            'successes': self.successes
        }

        with open(self.log_file, 'w') as f:
            json.dump(data, f, indent=2)

    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """
        Generate human-readable Markdown report.

        Returns
        -------
        str
            Path to report file
        """
        if output_path is None:
            output_path = self.report_file

        report = []
        report.append(f"# Experimental Report: {self.experiment_name}")
        report.append(f"\n**Session ID:** `{self.session_id}`")
        report.append(f"\n**Generated:** {datetime.now().isoformat()}\n")

        # System info
        report.append("## System Information")
        report.append(f"- Python: {self.system_info['python_version'].split()[0]}")
        report.append(f"- Platform: {self.system_info['platform']}")
        report.append(f"- NumPy: {self.system_info['numpy_version']}\n")

        # Preregistration
        if self.preregistration:
            report.append("## Preregistration (Immutable)")
            report.append(f"**Hypothesis:** {self.preregistration['hypothesis']}")
            report.append(f"\n**Prediction:** {self.preregistration['prediction']}")
            report.append(f"\n**Method:** {self.preregistration['method']}")
            if self.preregistration.get('falsifiability'):
                report.append(f"\n**Falsifiability:** {self.preregistration['falsifiability']}")
            report.append(f"\n**Hash:** `{self.preregistration['hash']}`")
            report.append(f"\n**Timestamp:** {self.preregistration['timestamp']}\n")

        # Results
        if self.results:
            report.append(f"## Results ({len(self.results)} entries)")
            report.append(f"Total experimental runs: {len(self.results)}\n")

        # Summary
        if self.summary:
            report.append("## Summary")
            for item in self.summary:
                report.append(f"- {item['message']}")
            report.append("")

        # Successes
        if self.successes:
            report.append("## ✓ Successes")
            for item in self.successes:
                report.append(f"- ✓ {item['message']}")
            report.append("")

        # Failures
        if self.failures:
            report.append("## ❌ Failures")
            for item in self.failures:
                report.append(f"- ❌ {item['message']}")
            report.append("")

        # Conclusion
        report.append("## Conclusion")
        total = len(self.successes) + len(self.failures)
        if total > 0:
            success_rate = len(self.successes) / total * 100
            report.append(f"**Success Rate:** {success_rate:.1f}% ({len(self.successes)}/{total})")

        report_text = "\n".join(report)

        with open(output_path, 'w') as f:
            f.write(report_text)

        print(f"\n📄 Report generated: {output_path}")
        return str(output_path)


def preregister_hypothesis(
    name: str,
    hypothesis: str,
    prediction: str,
    method: str,
    falsifiability: Optional[str] = None,
    output_dir: Optional[Path] = None
) -> AutoLogger:
    """
    Convenience function to create logger and preregister in one step.

    Parameters
    ----------
    name : str
        Experiment name
    hypothesis : str
        The hypothesis
    prediction : str
        Quantitative prediction
    method : str
        Method to test
    falsifiability : str, optional
        Falsification criteria
    output_dir : Path, optional
        Output directory

    Returns
    -------
    AutoLogger
        Initialized logger with preregistration
    """
    logger = AutoLogger(name, output_dir)
    logger.preregister(hypothesis, prediction, method, falsifiability)
    return logger
