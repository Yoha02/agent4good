import os
import random
import google.auth
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from ..tools.common_utils import COUNTY_STATE_MAPPING, infer_state_from_county
from typing import Optional, Tuple, Dict, List


INFECTIOUS_DISEASES = ["Salmonella", "E. coli", "Norovirus", "Hepatitis A", "Giardia", "Cryptosporidium"]


def get_infectious_disease_data(county: Optional[str] = None, state: Optional[str] = None, 
                                disease: Optional[str] = None, year: Optional[int] = None) -> dict:
    """Retrieves infectious disease data from CDC BEAM BigQuery dataset."""
    try:
        # Handle state inference from county
        if county and not state:
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
            print(f"[DISEASE] Querying for state: {state} -> {state_abbrev}")
        
        # Query CDC BEAM dataset
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-00-4a7d408c735c")
        
        # Build query
        where_conditions = []
        if state_abbrev:
            where_conditions.append(f"State = '{state_abbrev}'")
        if disease:
            where_conditions.append(f"LOWER(Pathogen) LIKE LOWER('%{disease}%')")
        if year:
            where_conditions.append(f"Year = {year}")
        else:
            where_conditions.append("Year = 2025")  # Default to recent data
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "Year = 2025"
        
        query = f"""
        SELECT 
            Year,
            Month,
            State,
            `Source Type` as Source_Type,
            Pathogen,
            `Serotype or Species` as Serotype_or_Species,
            SUM(`Number of isolates`) as total_cases
        FROM `{project_id}.beam_report_data_folder.beam_report_data`
        WHERE {where_clause}
        GROUP BY Year, Month, State, `Source Type`, Pathogen, `Serotype or Species`
        ORDER BY total_cases DESC
        LIMIT 50
        """
        
        # Execute query using standard BigQuery client with ADK credentials
        try:
            from google.cloud import bigquery
            
            application_default_credentials, _ = google.auth.default()
            
            # Use standard BigQuery client (ADK's BigQueryToolset.execute_sql doesn't exist)
            client = bigquery.Client(
                project=project_id,
                credentials=application_default_credentials
            )
            
            print(f"[DISEASE] Executing BigQuery query...")
            query_job = client.query(query)
            results = query_job.result()
            
            # Convert to expected format
            result_data = []
            for row in results:
                result_data.append(dict(row))
            
            print(f"[DISEASE] Query returned {len(result_data)} rows from CDC BEAM dataset")
            
            # Create result object matching expected format
            class QueryResult:
                def __init__(self, data):
                    self.status = "success" if data else "no_data"
                    self.data = data
            
            result = QueryResult(result_data)
            
            if result.status == "success" and result.data:
                # Process real data
                report_data = []
                total_cases = 0
                
                for row in result.data[:10]:  # Top 10 pathogens
                    cases = int(row.get('total_cases', 0))
                    pathogen = row.get('Pathogen', 'Unknown')
                    source = row.get('Source_Type', 'Unknown')
                    
                    report_data.append({
                        "disease": pathogen,
                        "cases": cases,
                        "source": source,
                        "serotype": row.get('Serotype_or_Species', 'N/A')
                    })
                    total_cases += cases
                
                location_desc = f"{state}" if state else "All States"
                year_text = f" in {year}" if year else " in 2025"
                
                report = f"""Infectious Disease Report for {location_desc}{year_text}:
(Data from CDC BEAM Dashboard via BigQuery)

Total Cases Reported: {total_cases}

Disease Breakdown:"""
                
                for data in report_data:
                    report += f"""
- {data['disease']}: {data['cases']} isolates (Source: {data['source']})"""
                
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
                # Fallback to mock data if query fails
                raise Exception("No data returned from BigQuery")
                
        except Exception as query_error:
            print(f"[DISEASE] BigQuery error: {query_error}")
            print(f"[DISEASE] Query was: {query[:200]}...")
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
        
        for data in report_data:
            report += f"""
- {data['disease']}: {data['cases']} cases"""
        
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