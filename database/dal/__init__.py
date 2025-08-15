"""Data Access Layer for Tiger System"""

from .base_dal import BaseDAL
from .opportunity_dal import OpportunityDAL

__all__ = [
    'BaseDAL',
    'OpportunityDAL'
]