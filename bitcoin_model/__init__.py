"""
Bitcoin Strategic Investment Model

A sophisticated Python framework for strategic Bitcoin investment decisions
based on macroeconomic indicators, on-chain metrics, and monetary policy analysis.
"""

from .core import BitcoinMacroModel
from .models.fed_pivot import FedPivotModel
from .models.m2_miner import M2MinerModel

__version__ = "3.0.0"
__author__ = "SBSHCMG"

__all__ = [
    "BitcoinMacroModel",
    "FedPivotModel", 
    "M2MinerModel"
]