# -*- coding: utf-8 -*-
"""HTML report generation for FileGuard timelines."""

from __future__ import annotations

import base64
import logging
from collections import Counter
from datetime import datetime
from io import BytesIO
from pathlib import Path

from fileguard.models import RiskAssessment

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Render a FileGuard alert timeline into an HTML report."""

    def __init__(self, template_path: str, output_path: str) -> None:
        """Initialize the report generator."""
        self.template_path = Path(template_path)
        self.output_path = Path(output_path)

    def generate(self, timeline: list[RiskAssessment]) -> None:
        """Generate an HTML report from a timeline of risk assessments."""
        from jinja2 import Template

        template = Template(self.template_path.read_text(encoding="utf-8"))
        level_counts = Counter(assessment.level.upper() for assessment in timeline)
        html = template.render(
            report_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            watch_dirs="N/A",
            total_events=len(timeline),
            critical_count=level_counts["CRITICAL"],
            high_count=level_counts["HIGH"],
            medium_count=level_counts["MEDIUM"],
            low_count=level_counts["LOW"],
            score_distribution_chart=self._build_score_distribution_chart(timeline),
            alerts=timeline,
        )

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(html, encoding="utf-8")
        logger.info("HTML report generated: %s", self.output_path.resolve())

    @staticmethod
    def _build_score_distribution_chart(timeline: list[RiskAssessment]) -> str:
        """Return a base64 PNG chart for risk score distribution."""
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except ImportError:
            logger.warning("matplotlib is not installed; report chart omitted.")
            return ""

        scores = [assessment.score for assessment in timeline]
        figure, axis = plt.subplots(figsize=(7, 3.5))
        if scores:
            axis.hist(scores, bins=[0, 3, 5, 7, 10], color="#4c78a8", edgecolor="#ffffff")
        else:
            axis.text(0.5, 0.5, "No alerts", ha="center", va="center", transform=axis.transAxes)
        axis.set_title("Risk Score Distribution")
        axis.set_xlabel("Score")
        axis.set_ylabel("Count")
        axis.set_xlim(0, 10)
        axis.grid(axis="y", alpha=0.25)
        figure.tight_layout()

        buffer = BytesIO()
        figure.savefig(buffer, format="png", dpi=140)
        plt.close(figure)
        return base64.b64encode(buffer.getvalue()).decode("ascii")
