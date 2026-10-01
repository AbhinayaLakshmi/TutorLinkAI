"""
TutorLinkAI — Research Visualization & Statistical Reporting Module.
"""
from evaluation.research.visualization.generate_tables import generate_all_tables
from evaluation.research.visualization.generate_figures import generate_all_figures
from evaluation.research.visualization.generate_report import generate_research_report

__all__ = [
    "generate_all_tables",
    "generate_all_figures",
    "generate_research_report",
]
