"""
Core Utility Package for Quant Research
"""
from .Logger import logger
from .DataManager import DataProvider, normalize_series
from .NavAnalyzer import NavAnalyzer, Visualizer, PerformanceReport
from .TSCompare import TSComparator
from .NumericalOperators import FactorOperators
from .SparseSignalTester import SparseSignalTester
from .TimingTester import TimingTester

__all__ = [
    'logger',
    'DataProvider',
    'normalize_series',
    'NavAnalyzer',
    'Visualizer',
    'PerformanceReport',
    'TSComparator',
    'FactorOperators',
    'SparseSignalTester',
    'TimingTester'
]
