# ./tools/common_utils.py
import datetime
from typing import Optional, Tuple

# Mapping reused by both modules
COUNTY_STATE_MAPPING = {
    "Los Angeles": "California", "Cook": "Illinois", "Harris": "Texas",
    "Maricopa": "Arizona", "San Diego": "California", "Orange": ["California", "Florida"],
    "Miami-Dade": "Florida", "King": "Washington", "Dallas": "Texas", "Wayne": "Michigan",
    "Santa Clara": "California", "Alameda": "California", "Broward": "Florida",
    "Riverside": "California", "Queens": "New York", "Tarrant": "Texas", "Bexar": "Texas",
    "Clark": ["Nevada", "Washington"], "Middlesex": ["Massachusetts", "New Jersey"],
    "Fairfax": "Virginia", "Suffolk": ["Massachusetts", "New York"],
    "Montgomery": ["Maryland", "Pennsylvania", "Texas"], "Fulton": "Georgia",
    "Cuyahoga": "Ohio", "Milwaukee": "Wisconsin", "Baltimore": "Maryland",
    "Hennepin": "Minnesota", "Allegheny": "Pennsylvania",
    "Franklin": ["Ohio", "Pennsylvania"], "Jefferson": ["Alabama", "Colorado", "Kentucky", "Louisiana"],
    "Washington": ["Oregon", "Pennsylvania", "Utah"],
    "Jackson": ["Missouri", "Mississippi"],
    "Madison": ["Alabama", "Illinois", "Indiana", "Mississippi", "Tennessee"],
    "Lincoln": [
        "Nebraska", "Nevada", "New Mexico", "North Carolina", "Oklahoma",
        "Oregon", "South Dakota", "Tennessee", "Washington", "West Virginia", "Wyoming"
    ],
}


def infer_state_from_county(county: str) -> Tuple[Optional[str], bool]:
    """Infer state name from a county using COUNTY_STATE_MAPPING."""
    county_lower = county.lower().strip()
    for name, state_info in COUNTY_STATE_MAPPING.items():
        if name.lower() == county_lower:
            if isinstance(state_info, str):
                return state_info, False
            return None, True
    return None, False


def handle_relative_dates(days_back: int) -> Tuple[int, int, int]:
    """
    Converts relative days (days_back) into absolute year, month, and day.
    Based on reference cutoff date 2021-11-08 from the EPA dataset.
    """
    cutoff_date = datetime.date(2021, 11, 8)
    target_date = cutoff_date - datetime.timedelta(days=days_back)
    return target_date.year, target_date.month, target_date.day
