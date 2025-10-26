import json
from typing import Dict, List, Optional

class LocationService:
    """
    Service for managing location hierarchy and filters (State -> City -> County -> ZIP)
    """
    
    def __init__(self):
        # US States with major cities and counties
        self.location_data = {
            'AL': {
                'name': 'Alabama',
                'cities': {
                    'Birmingham': {'counties': ['Jefferson'], 'zipcodes': ['35201', '35203', '35205']},
                    'Montgomery': {'counties': ['Montgomery'], 'zipcodes': ['36104', '36106', '36108']},
                    'Mobile': {'counties': ['Mobile'], 'zipcodes': ['36601', '36602', '36604']}
                }
            },
            'AK': {
                'name': 'Alaska',
                'cities': {
                    'Anchorage': {'counties': ['Anchorage'], 'zipcodes': ['99501', '99502', '99503']},
                    'Fairbanks': {'counties': ['Fairbanks North Star'], 'zipcodes': ['99701', '99702', '99703']}
                }
            },
            'AZ': {
                'name': 'Arizona',
                'cities': {
                    'Phoenix': {'counties': ['Maricopa'], 'zipcodes': ['85001', '85003', '85004', '85006']},
                    'Tucson': {'counties': ['Pima'], 'zipcodes': ['85701', '85702', '85703', '85704']}
                }
            },
            'AR': {
                'name': 'Arkansas',
                'cities': {
                    'Little Rock': {'counties': ['Pulaski'], 'zipcodes': ['72201', '72202', '72203', '72204']}
                }
            },
            'CA': {
                'name': 'California',
                'cities': {
                    'Los Angeles': {'counties': ['Los Angeles'], 'zipcodes': ['90001', '90002', '90003', '90004']},
                    'San Francisco': {'counties': ['San Francisco'], 'zipcodes': ['94102', '94103', '94104', '94105']},
                    'San Diego': {'counties': ['San Diego'], 'zipcodes': ['92101', '92102', '92103', '92104']},
                    'Sacramento': {'counties': ['Sacramento'], 'zipcodes': ['95814', '95815', '95816', '95817']}
                }
            },
            'CO': {
                'name': 'Colorado',
                'cities': {
                    'Denver': {'counties': ['Denver'], 'zipcodes': ['80201', '80202', '80203', '80204']},
                    'Colorado Springs': {'counties': ['El Paso'], 'zipcodes': ['80901', '80902', '80903']}
                }
            },
            'CT': {
                'name': 'Connecticut',
                'cities': {
                    'Hartford': {'counties': ['Hartford'], 'zipcodes': ['06101', '06103', '06105']},
                    'New Haven': {'counties': ['New Haven'], 'zipcodes': ['06510', '06511', '06519']}
                }
            },
            'DE': {
                'name': 'Delaware',
                'cities': {
                    'Wilmington': {'counties': ['New Castle'], 'zipcodes': ['19801', '19802', '19803']}
                }
            },
            'FL': {
                'name': 'Florida',
                'cities': {
                    'Miami': {'counties': ['Miami-Dade'], 'zipcodes': ['33101', '33102', '33109', '33111']},
                    'Tampa': {'counties': ['Hillsborough'], 'zipcodes': ['33601', '33602', '33603', '33604']},
                    'Orlando': {'counties': ['Orange'], 'zipcodes': ['32801', '32802', '32803', '32804']},
                    'Jacksonville': {'counties': ['Duval'], 'zipcodes': ['32201', '32202', '32203', '32204']}
                }
            },
            'GA': {
                'name': 'Georgia',
                'cities': {
                    'Atlanta': {'counties': ['Fulton'], 'zipcodes': ['30301', '30303', '30305', '30308']},
                    'Savannah': {'counties': ['Chatham'], 'zipcodes': ['31401', '31404', '31405']}
                }
            },
            'HI': {
                'name': 'Hawaii',
                'cities': {
                    'Honolulu': {'counties': ['Honolulu'], 'zipcodes': ['96801', '96813', '96814', '96815']}
                }
            },
            'ID': {
                'name': 'Idaho',
                'cities': {
                    'Boise': {'counties': ['Ada'], 'zipcodes': ['83701', '83702', '83703', '83704']}
                }
            },
            'IL': {
                'name': 'Illinois',
                'cities': {
                    'Chicago': {'counties': ['Cook'], 'zipcodes': ['60601', '60602', '60603', '60604']},
                    'Springfield': {'counties': ['Sangamon'], 'zipcodes': ['62701', '62702', '62703', '62704']},
                    'Peoria': {'counties': ['Peoria'], 'zipcodes': ['61601', '61602', '61603', '61604']}
                }
            },
            'IN': {
                'name': 'Indiana',
                'cities': {
                    'Indianapolis': {'counties': ['Marion'], 'zipcodes': ['46201', '46202', '46203', '46204']}
                }
            },
            'IA': {
                'name': 'Iowa',
                'cities': {
                    'Des Moines': {'counties': ['Polk'], 'zipcodes': ['50301', '50309', '50310', '50311']}
                }
            },
            'KS': {
                'name': 'Kansas',
                'cities': {
                    'Wichita': {'counties': ['Sedgwick'], 'zipcodes': ['67201', '67202', '67203', '67204']}
                }
            },
            'KY': {
                'name': 'Kentucky',
                'cities': {
                    'Louisville': {'counties': ['Jefferson'], 'zipcodes': ['40201', '40202', '40203', '40204']}
                }
            },
            'LA': {
                'name': 'Louisiana',
                'cities': {
                    'New Orleans': {'counties': ['Orleans'], 'zipcodes': ['70112', '70113', '70115', '70116']},
                    'Baton Rouge': {'counties': ['East Baton Rouge'], 'zipcodes': ['70801', '70802', '70803']}
                }
            },
            'ME': {
                'name': 'Maine',
                'cities': {
                    'Portland': {'counties': ['Cumberland'], 'zipcodes': ['04101', '04102', '04103', '04104']}
                }
            },
            'MD': {
                'name': 'Maryland',
                'cities': {
                    'Baltimore': {'counties': ['Baltimore City'], 'zipcodes': ['21201', '21202', '21205', '21218']}
                }
            },
            'MA': {
                'name': 'Massachusetts',
                'cities': {
                    'Boston': {'counties': ['Suffolk'], 'zipcodes': ['02101', '02108', '02109', '02110']},
                    'Worcester': {'counties': ['Worcester'], 'zipcodes': ['01601', '01602', '01603']}
                }
            },
            'MI': {
                'name': 'Michigan',
                'cities': {
                    'Detroit': {'counties': ['Wayne'], 'zipcodes': ['48201', '48202', '48203', '48204']},
                    'Grand Rapids': {'counties': ['Kent'], 'zipcodes': ['49501', '49503', '49504']}
                }
            },
            'MN': {
                'name': 'Minnesota',
                'cities': {
                    'Minneapolis': {'counties': ['Hennepin'], 'zipcodes': ['55401', '55402', '55403', '55404']},
                    'Saint Paul': {'counties': ['Ramsey'], 'zipcodes': ['55101', '55102', '55103', '55104']}
                }
            },
            'MS': {
                'name': 'Mississippi',
                'cities': {
                    'Jackson': {'counties': ['Hinds'], 'zipcodes': ['39201', '39202', '39203', '39204']}
                }
            },
            'MO': {
                'name': 'Missouri',
                'cities': {
                    'Kansas City': {'counties': ['Jackson'], 'zipcodes': ['64101', '64102', '64105', '64106']},
                    'Saint Louis': {'counties': ['St. Louis City'], 'zipcodes': ['63101', '63102', '63103', '63104']}
                }
            },
            'MT': {
                'name': 'Montana',
                'cities': {
                    'Billings': {'counties': ['Yellowstone'], 'zipcodes': ['59101', '59102', '59105']}
                }
            },
            'NE': {
                'name': 'Nebraska',
                'cities': {
                    'Omaha': {'counties': ['Douglas'], 'zipcodes': ['68101', '68102', '68104', '68105']}
                }
            },
            'NV': {
                'name': 'Nevada',
                'cities': {
                    'Las Vegas': {'counties': ['Clark'], 'zipcodes': ['89101', '89102', '89103', '89104']},
                    'Reno': {'counties': ['Washoe'], 'zipcodes': ['89501', '89502', '89503']}
                }
            },
            'NH': {
                'name': 'New Hampshire',
                'cities': {
                    'Manchester': {'counties': ['Hillsborough'], 'zipcodes': ['03101', '03102', '03103', '03104']}
                }
            },
            'NJ': {
                'name': 'New Jersey',
                'cities': {
                    'Newark': {'counties': ['Essex'], 'zipcodes': ['07101', '07102', '07103', '07104']},
                    'Jersey City': {'counties': ['Hudson'], 'zipcodes': ['07302', '07304', '07305']}
                }
            },
            'NM': {
                'name': 'New Mexico',
                'cities': {
                    'Albuquerque': {'counties': ['Bernalillo'], 'zipcodes': ['87101', '87102', '87104', '87105']}
                }
            },
            'NY': {
                'name': 'New York',
                'cities': {
                    'New York City': {'counties': ['New York', 'Kings', 'Queens', 'Bronx', 'Richmond'], 'zipcodes': ['10001', '10002', '10003', '10004']},
                    'Buffalo': {'counties': ['Erie'], 'zipcodes': ['14201', '14202', '14203', '14204']},
                    'Albany': {'counties': ['Albany'], 'zipcodes': ['12201', '12202', '12203', '12204']},
                    'Rochester': {'counties': ['Monroe'], 'zipcodes': ['14601', '14602', '14603', '14604']}
                }
            },
            'NC': {
                'name': 'North Carolina',
                'cities': {
                    'Charlotte': {'counties': ['Mecklenburg'], 'zipcodes': ['28201', '28202', '28203', '28204']},
                    'Raleigh': {'counties': ['Wake'], 'zipcodes': ['27601', '27603', '27604', '27605']}
                }
            },
            'ND': {
                'name': 'North Dakota',
                'cities': {
                    'Fargo': {'counties': ['Cass'], 'zipcodes': ['58102', '58103', '58104']}
                }
            },
            'OH': {
                'name': 'Ohio',
                'cities': {
                    'Columbus': {'counties': ['Franklin'], 'zipcodes': ['43201', '43202', '43203', '43204']},
                    'Cleveland': {'counties': ['Cuyahoga'], 'zipcodes': ['44101', '44102', '44103', '44104']},
                    'Cincinnati': {'counties': ['Hamilton'], 'zipcodes': ['45201', '45202', '45203', '45204']}
                }
            },
            'OK': {
                'name': 'Oklahoma',
                'cities': {
                    'Oklahoma City': {'counties': ['Oklahoma'], 'zipcodes': ['73101', '73102', '73103', '73104']},
                    'Tulsa': {'counties': ['Tulsa'], 'zipcodes': ['74101', '74103', '74104', '74105']}
                }
            },
            'OR': {
                'name': 'Oregon',
                'cities': {
                    'Portland': {'counties': ['Multnomah'], 'zipcodes': ['97201', '97202', '97204', '97205']},
                    'Eugene': {'counties': ['Lane'], 'zipcodes': ['97401', '97402', '97403']}
                }
            },
            'PA': {
                'name': 'Pennsylvania',
                'cities': {
                    'Philadelphia': {'counties': ['Philadelphia'], 'zipcodes': ['19101', '19102', '19103', '19104']},
                    'Pittsburgh': {'counties': ['Allegheny'], 'zipcodes': ['15201', '15202', '15203', '15204']}
                }
            },
            'RI': {
                'name': 'Rhode Island',
                'cities': {
                    'Providence': {'counties': ['Providence'], 'zipcodes': ['02901', '02903', '02904', '02905']}
                }
            },
            'SC': {
                'name': 'South Carolina',
                'cities': {
                    'Charleston': {'counties': ['Charleston'], 'zipcodes': ['29401', '29403', '29407', '29412']},
                    'Columbia': {'counties': ['Richland'], 'zipcodes': ['29201', '29203', '29204', '29205']}
                }
            },
            'SD': {
                'name': 'South Dakota',
                'cities': {
                    'Sioux Falls': {'counties': ['Minnehaha'], 'zipcodes': ['57101', '57103', '57104', '57105']}
                }
            },
            'TN': {
                'name': 'Tennessee',
                'cities': {
                    'Nashville': {'counties': ['Davidson'], 'zipcodes': ['37201', '37203', '37204', '37205']},
                    'Memphis': {'counties': ['Shelby'], 'zipcodes': ['38101', '38103', '38104', '38105']}
                }
            },
            'TX': {
                'name': 'Texas',
                'cities': {
                    'Houston': {'counties': ['Harris'], 'zipcodes': ['77001', '77002', '77003', '77004']},
                    'Dallas': {'counties': ['Dallas'], 'zipcodes': ['75201', '75202', '75203', '75204']},
                    'Austin': {'counties': ['Travis'], 'zipcodes': ['78701', '78702', '78703', '78704']},
                    'San Antonio': {'counties': ['Bexar'], 'zipcodes': ['78201', '78202', '78203', '78204']}
                }
            },
            'UT': {
                'name': 'Utah',
                'cities': {
                    'Salt Lake City': {'counties': ['Salt Lake'], 'zipcodes': ['84101', '84102', '84103', '84104']}
                }
            },
            'VT': {
                'name': 'Vermont',
                'cities': {
                    'Burlington': {'counties': ['Chittenden'], 'zipcodes': ['05401', '05403', '05404', '05405']}
                }
            },
            'VA': {
                'name': 'Virginia',
                'cities': {
                    'Richmond': {'counties': ['Richmond City'], 'zipcodes': ['23218', '23219', '23220', '23221']},
                    'Virginia Beach': {'counties': ['Virginia Beach City'], 'zipcodes': ['23451', '23452', '23454']}
                }
            },
            'WA': {
                'name': 'Washington',
                'cities': {
                    'Seattle': {'counties': ['King'], 'zipcodes': ['98101', '98102', '98103', '98104']},
                    'Spokane': {'counties': ['Spokane'], 'zipcodes': ['99201', '99202', '99203', '99204']}
                }
            },
            'WV': {
                'name': 'West Virginia',
                'cities': {
                    'Charleston': {'counties': ['Kanawha'], 'zipcodes': ['25301', '25302', '25304', '25311']}
                }
            },
            'WI': {
                'name': 'Wisconsin',
                'cities': {
                    'Milwaukee': {'counties': ['Milwaukee'], 'zipcodes': ['53201', '53202', '53203', '53204']},
                    'Madison': {'counties': ['Dane'], 'zipcodes': ['53701', '53703', '53704', '53705']}
                }
            },
            'WY': {
                'name': 'Wyoming',
                'cities': {
                    'Cheyenne': {'counties': ['Laramie'], 'zipcodes': ['82001', '82002', '82003', '82007']}
                }
            }
        }
    
    def get_all_states(self) -> List[Dict]:
        """Get all available states"""
        states = []
        for code, data in self.location_data.items():
            states.append({
                'code': code,
                'name': data['name'],
                'cities_count': len(data['cities'])
            })
        return sorted(states, key=lambda x: x['name'])
    
    def get_state_code_from_name(self, state_name: str) -> Optional[str]:
        """Convert state name to state code"""
        if not state_name:
            return None
        
        state_name_lower = state_name.strip().lower()
        for code, data in self.location_data.items():
            if data['name'].lower() == state_name_lower:
                return code
        return None
    
    def get_cities_by_state(self, state_code: str) -> List[Dict]:
        """Get all cities in a state"""
        if state_code not in self.location_data:
            return []
        
        cities = []
        state_data = self.location_data[state_code]
        
        for city_name, city_data in state_data['cities'].items():
            cities.append({
                'name': city_name,
                'state_code': state_code,
                'state_name': state_data['name'],
                'counties_count': len(city_data['counties']),
                'zipcodes_count': len(city_data['zipcodes'])
            })
        
        return sorted(cities, key=lambda x: x['name'])
    
    def get_counties_by_city(self, state_code: str, city_name: str) -> List[Dict]:
        """Get all counties in a city"""
        if state_code not in self.location_data:
            return []
        
        state_data = self.location_data[state_code]
        if city_name not in state_data['cities']:
            return []
        
        counties = []
        city_data = state_data['cities'][city_name]
        
        for county in city_data['counties']:
            counties.append({
                'name': county,
                'city': city_name,
                'state_code': state_code,
                'state_name': state_data['name']
            })
        
        return counties
    
    def get_zipcodes_by_location(self, state_code: str, city_name: str = None, county_name: str = None) -> List[Dict]:
        """Get ZIP codes by location"""
        if state_code not in self.location_data:
            return []
        
        state_data = self.location_data[state_code]
        zipcodes = []
        
        if city_name:
            if city_name not in state_data['cities']:
                return []
            
            city_data = state_data['cities'][city_name]
            for zipcode in city_data['zipcodes']:
                # If county filter is specified, check if city has that county
                if county_name and county_name not in city_data['counties']:
                    continue
                
                zipcodes.append({
                    'zipcode': zipcode,
                    'city': city_name,
                    'county': city_data['counties'][0],  # First county for the city
                    'state_code': state_code,
                    'state_name': state_data['name']
                })
        else:
            # Get all ZIP codes for the state
            for city_name, city_data in state_data['cities'].items():
                for zipcode in city_data['zipcodes']:
                    if county_name and county_name not in city_data['counties']:
                        continue
                    
                    zipcodes.append({
                        'zipcode': zipcode,
                        'city': city_name,
                        'county': city_data['counties'][0],
                        'state_code': state_code,
                        'state_name': state_data['name']
                    })
        
        return sorted(zipcodes, key=lambda x: x['zipcode'])
    
    def get_location_info(self, zipcode: str = None, state_code: str = None, 
                         city_name: str = None, county_name: str = None) -> Optional[Dict]:
        """Get complete location information"""
        
        if zipcode:
            # Find location by ZIP code
            for state_code, state_data in self.location_data.items():
                for city_name, city_data in state_data['cities'].items():
                    if zipcode in city_data['zipcodes']:
                        return {
                            'zipcode': zipcode,
                            'city': city_name,
                            'county': city_data['counties'][0],
                            'state_code': state_code,
                            'state_name': state_data['name'],
                            'coordinates': self._get_approximate_coordinates(state_code, city_name)
                        }
        
        elif state_code and city_name:
            if state_code in self.location_data and city_name in self.location_data[state_code]['cities']:
                city_data = self.location_data[state_code]['cities'][city_name]
                return {
                    'city': city_name,
                    'county': city_data['counties'][0] if county_name is None else county_name,
                    'state_code': state_code,
                    'state_name': self.location_data[state_code]['name'],
                    'zipcodes': city_data['zipcodes'],
                    'coordinates': self._get_approximate_coordinates(state_code, city_name)
                }
        
        return None
    
    def _get_approximate_coordinates(self, state_code: str, city_name: str) -> Dict:
        """Get approximate coordinates for major cities"""
        coordinates = {
            'CA': {
                'Los Angeles': {'lat': 34.0522, 'lon': -118.2437},
                'San Francisco': {'lat': 37.7749, 'lon': -122.4194},
                'San Diego': {'lat': 32.7157, 'lon': -117.1611},
                'Sacramento': {'lat': 38.5816, 'lon': -121.4944}
            },
            'NY': {
                'New York City': {'lat': 40.7128, 'lon': -74.0060},
                'Buffalo': {'lat': 42.8864, 'lon': -78.8784},
                'Albany': {'lat': 42.6526, 'lon': -73.7562},
                'Rochester': {'lat': 43.1566, 'lon': -77.6088}
            },
            'TX': {
                'Houston': {'lat': 29.7604, 'lon': -95.3698},
                'Dallas': {'lat': 32.7767, 'lon': -96.7970},
                'Austin': {'lat': 30.2672, 'lon': -97.7431},
                'San Antonio': {'lat': 29.4241, 'lon': -98.4936}
            },
            'FL': {
                'Miami': {'lat': 25.7617, 'lon': -80.1918},
                'Tampa': {'lat': 27.9506, 'lon': -82.4572},
                'Orlando': {'lat': 28.5383, 'lon': -81.3792},
                'Jacksonville': {'lat': 30.3322, 'lon': -81.6557}
            },
            'IL': {
                'Chicago': {'lat': 41.8781, 'lon': -87.6298},
                'Springfield': {'lat': 39.7817, 'lon': -89.6501},
                'Peoria': {'lat': 40.6936, 'lon': -89.5890}
            }
        }
        
        if state_code in coordinates and city_name in coordinates[state_code]:
            return coordinates[state_code][city_name]
        
        # Default coordinates (center of US)
        return {'lat': 39.8283, 'lon': -98.5795}
    
    def search_locations(self, query: str) -> List[Dict]:
        """Search locations by name or ZIP code"""
        results = []
        query = query.lower().strip()
        
        # Check if query is a ZIP code
        if query.isdigit() and len(query) == 5:
            location = self.get_location_info(zipcode=query)
            if location:
                results.append({
                    'type': 'zipcode',
                    'match': query,
                    'location': location
                })
        
        # Search states
        for state_code, state_data in self.location_data.items():
            if (query in state_data['name'].lower() or 
                query in state_code.lower()):
                results.append({
                    'type': 'state',
                    'match': state_data['name'],
                    'location': {
                        'state_code': state_code,
                        'state_name': state_data['name']
                    }
                })
        
        # Search cities
        for state_code, state_data in self.location_data.items():
            for city_name in state_data['cities']:
                if query in city_name.lower():
                    results.append({
                        'type': 'city',
                        'match': city_name,
                        'location': {
                            'city': city_name,
                            'state_code': state_code,
                            'state_name': state_data['name'],
                            'coordinates': self._get_approximate_coordinates(state_code, city_name)
                        }
                    })
        
        return results[:10]  # Limit to 10 results