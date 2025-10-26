import os
import random
import google.auth
from google.cloud import bigquery
from ..tools.common_utils import COUNTY_STATE_MAPPING, infer_state_from_county
from typing import Optional, Tuple, Dict, List


INFECTIOUS_DISEASES = ["Salmonella", "E. coli", "Norovirus", "Hepatitis A", "Giardia", "Cryptosporidium"]

# Disease synonym mapping - maps user-friendly names to actual CDC BEAM database names
DISEASE_SYNONYMS = {
    "e. coli": "STEC",
    "e coli": "STEC",
    "escherichia coli": "STEC",
    "e.coli": "STEC",
    "stec": "STEC",
    "stec o157": "STEC",
    "shiga toxin-producing e. coli": "STEC",
    "shiga toxin producing e coli": "STEC",
}


def get_infectious_disease_data(county: Optional[str] = None, state: Optional[str] = None, 
                                disease: Optional[str] = None, year: Optional[int] = None,
                                start_year: Optional[int] = None, end_year: Optional[int] = None) -> dict:
    """Retrieves infectious disease data from CDC BEAM BigQuery dataset.
    
    Supports both single year (year parameter) and year ranges (start_year/end_year).
    Use year for a single year, or start_year + end_year for a range (e.g., 2019-2021).
    """
    try:
        # Handle state inference from county
        if county and not state:
            print(f"[DISEASE] Received county query: {county}")
            print(f"[DISEASE] Note: CDC BEAM data is at STATE level, not county level. Will query state data for county's state.")
            inferred_state, is_ambiguous = infer_state_from_county(county)
            if is_ambiguous:
                county_lower = county.lower().strip()
                for county_name, state_info in COUNTY_STATE_MAPPING.items():
                    if county_name.lower() == county_lower and isinstance(state_info, list):
                        return {
                            "status": "ambiguous",
                            "error_message": f"County '{county}' exists in multiple states: {', '.join(state_info)}. Please specify which state.",
                            "possible_states": state_info
                        }
            elif inferred_state:
                state = inferred_state
                print(f"[DISEASE] Mapped county '{county}' to state '{state}'")
            else:
                print(f"[DISEASE] Warning: Could not infer state from county '{county}'")
        
        if county:
            print(f"[DISEASE] Warning: County '{county}' specified but CDC data is state-level only. Querying state-level data.")
        
        # Get state abbreviation for query
        state_abbrev = None
        if state:
            # Map full state name to abbreviation (CDC data uses 2-letter codes)
            state_map = {
                'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
                'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
                'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
                'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
                'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
                'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
                'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
                'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
                'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
                'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
                'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
                'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
                'Wisconsin': 'WI', 'Wyoming': 'WY'
            }
            state_abbrev = state_map.get(state, state[:2].upper() if len(state) > 2 else state.upper())
            print(f"[DISEASE] Query parameters: state={state} ({state_abbrev}), county={county}, disease={disease}, year={year}, start={start_year}, end={end_year}")
        
        # Query CDC BEAM dataset
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-00-4a7d408c735c")
        
        # Build query
        where_conditions = []
        if state_abbrev:
            where_conditions.append(f"State = '{state_abbrev}'")
        if disease:
            # Check for disease synonym
            disease_lower = disease.lower().strip()
            mapped_disease = DISEASE_SYNONYMS.get(disease_lower, disease)
            if mapped_disease != disease:
                print(f"[DISEASE] Mapped disease '{disease}' to '{mapped_disease}'")
                disease = mapped_disease
            
            where_conditions.append(f"LOWER(Pathogen) LIKE LOWER('%{disease}%')")
        
        # Handle year range vs single year
        if start_year and end_year:
            where_conditions.append(f"Year >= {start_year} AND Year <= {end_year}")
        elif year:
            where_conditions.append(f"Year = {year}")
        else:
            where_conditions.append("Year = 2025")  # Default to recent data
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "Year = 2025"
        
        query = f"""
        SELECT 
            Year,
            Month,
            State,
            `Source Type`,
            Pathogen,
            `Serotype or Species`,
            SUM(`Number of isolates`) as total_cases
        FROM `{project_id}.beam_report_data_folder.beam_report_data`
        WHERE {where_clause}
        GROUP BY Year, Month, State, `Source Type`, Pathogen, `Serotype or Species`
        ORDER BY total_cases DESC
        LIMIT 50
        """
        
        # Execute query using standard BigQuery client
        try:
            # Debug: Print the full query
            print(f"[DISEASE] Executing query on project: {project_id}")
            print(f"[DISEASE] Full query:")
            print(query)
            
            # Initialize BigQuery client
            bq_client = bigquery.Client(project=project_id)
            
            # Execute query
            query_job = bq_client.query(query)
            results = query_job.result()
            data = list(results)
            
            print(f"[DISEASE] Query returned {len(data)} rows")
            
            if data:
                # Process real data
                report_data = []
                total_cases = 0
                
                for row in data[:10]:  # Top 10 pathogens
                    row_dict = dict(row)
                    cases = int(row_dict.get('total_cases', 0))
                    pathogen = row_dict.get('Pathogen', 'Unknown')
                    source = row_dict.get('Source Type', 'Unknown')
                    
                    report_data.append({
                        "disease": pathogen,
                        "cases": cases,
                        "source": source,
                        "serotype": row_dict.get('Serotype or Species', 'N/A')
                    })
                    total_cases += cases
                
                location_desc = f"{county}, {state}" if county and state else f"{state}" if state else "All States"
                year_text = f" in {year}" if year else f" in {start_year}-{end_year}" if start_year and end_year else " in 2025"
                
                # Add note about county if specified
                county_note = f"\nNote: Data shown is for {state} state level. County-specific data is not available in CDC BEAM dataset.\n" if county else ""
                
                report = f"""Infectious Disease Report for {location_desc}{year_text}:{county_note}
(Data from CDC BEAM Dashboard via BigQuery)

Total Cases Reported: {total_cases}

Disease Breakdown:"""
                
                for disease_data in report_data:
                    report += f"""
- {disease_data['disease']}: {disease_data['cases']} isolates (Source: {disease_data['source']})"""
                
                report += f"""

Data Source: CDC BEAM Dashboard Report
Note: Data represents laboratory-confirmed isolates reported to surveillance systems."""
                
                return {
                    "status": "success",
                    "report": report,
                    "data": {
                        "location": location_desc,
                        "total_cases": total_cases,
                        "diseases": report_data
                    }
                }
            else:
                # No data returned - try to help user with available data
                print(f"[DISEASE] Query returned no data rows")
                
                # Try to get available pathogens for this query
                try:
                    help_query = f"""
                    SELECT DISTINCT Pathogen
                    FROM `{project_id}.beam_report_data_folder.beam_report_data`
                    WHERE {where_clause.split(' AND LOWER(Pathogen)')[0]}  -- Remove disease filter
                    LIMIT 20
                    """
                    help_job = bq_client.query(help_query)
                    available_pathogens = [row[0] for row in help_job.result()]
                    
                    if available_pathogens:
                        print(f"[DISEASE] Available pathogens for this query: {', '.join(available_pathogens)}")
                        available_msg = f" Available pathogens: {', '.join(available_pathogens)}"
                    else:
                        available_msg = ""
                except Exception as e:
                    print(f"[DISEASE] Could not fetch available pathogens: {e}")
                    available_msg = ""
                
                raise Exception(f"No data returned from BigQuery.{available_msg}")
                
        except Exception as query_error:
            error_str = str(query_error)
            print(f"[DISEASE] BigQuery error: {error_str}")
            print(f"[DISEASE] Query was: {query[:200]}...")
            
            # Check if error contains available pathogens info
            if "Available pathogens:" in error_str:
                # Don't use mock data - return helpful error
                return {
                    "status": "error",
                    "error_message": f"No data found for disease '{disease or 'specified disease'}' in the CDC BEAM database. {error_str}",
                    "suggestion": "Try querying for: STEC, Salmonella, Campylobacter, Shigella, or Vibrio"
                }
            
            print(f"[DISEASE] Falling back to mock data")
            # Generate mock data as fallback
            location_desc = f"{county}, {state}" if county and state else state if state else "Demo Location"
            diseases_to_report = [disease] if disease else random.sample(INFECTIOUS_DISEASES, 3)
            
            report_data = []
            total_cases = 0
            
            for disease_name in diseases_to_report:
                cases = random.randint(15, 250)
                report_data.append({
                    "disease": disease_name,
                    "cases": cases,
                    "source": "Mock Data"
                })
                total_cases += cases
            
            year_text = f" in {year}" if year else " (demo data)"
            
            report = f"""Infectious Disease Report for {location_desc}{year_text}:
(Demo Mode - Real data requires BigQuery access)

Total Cases Reported: {total_cases}

Disease Breakdown:"""
            
            for disease_data in report_data:
                report += f"""
- {disease_data['disease']}: {disease_data['cases']} cases"""
            
            return {
                "status": "success",
                "report": report,
                "data": {
                    "location": location_desc,
                    "total_cases": total_cases,
                    "diseases": report_data
                }
            }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error retrieving infectious disease data: {str(e)}"
        }