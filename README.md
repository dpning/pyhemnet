# PyHemnet

[![PyPI version](https://img.shields.io/pypi/v/pyhemnet)](https://pypi.org/project/pyhemnet/)
[![Python versions](https://img.shields.io/pypi/pyversions/pyhemnet.svg)](https://pypi.org/project/pyhemnet/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/pyhemnet/month)](https://pepy.tech/project/pyhemnet)

A Python library for accessing Swedish real estate and rental property data from Hemnet.se and Qasa.se. Extract property sales information, rental listings, prices, locations, and detailed property characteristics.

## Features

- 🏠 **Hemnet Data Access**: Access property sales data from Hemnet.se
  - Get summary statistics on properties for sale and sold properties
  - Extract detailed information including prices, location, size, broker, and more
  - Filter by location and property types
  - Support for multiple property types (villa, radhus, bostadsrätt, etc.)

- 🏘️ **Qasa Rental Data**: Access rental property data from Qasa.se
  - Search for available rental homes by location
  - Get detailed rental information including landlord details, fees, and requirements
  - Filter by property type, price range, furnishing, and more
  - Support for long-term rentals across Sweden

- 🚀 Easy-to-use Python API
- 💻 Object-oriented design with clean interfaces

## Installation

Install from PyPI:

```bash
pip install pyhemnet
```

Or install from source:

```bash
git clone https://github.com/ningdp2012/pyhemnet.git
cd pyhemnet
pip install -e .
```

## Quick Start

### Hemnet - Property Sales Data

```python
from pyhemnet import HemnetScraper, HemnetItemType

# Create a scraper instance
scraper = HemnetScraper()

# Get summary statistics
listing_count, sold_count = scraper.get_summary(location_id="17744")
print(f"Properties for sale: {listing_count}")
print(f"Sold properties: {sold_count}")

# Get detailed sold properties
homes = scraper.get_sold(
    location_id="17744",
    item_types=[HemnetItemType.VILLA, HemnetItemType.RADHUS]
)

for home in homes:
    print(f"{home['address']} - {home['final_price']} SEK")
```

### Qasa - Rental Property Data

```python
from pyhemnet import QasaScraper

# Create a scraper instance
scraper = QasaScraper()

# Search for rental homes
homes = scraper.get_homes(
    area_identifier="se/helsingborg",
    home_types=["apartment", "house"],
    min_monthly_cost=5000,
    max_monthly_cost=15000
)

for home in homes:
    print(f"{home['title']} - {home['rent']} {home['currency']}/month")
    print(f"Location: {home['locality']}")
    print(f"Rooms: {home['rooms']}, Size: {home['square_meters']} m²")
    print("---")

# Get detailed information for a specific home
details = scraper.get_home_details(home_id="12345")
print(f"Description: {details['description']}")
print(f"Landlord: {details['landlord']}")
```

## Usage

### Hemnet API

#### Initialize the Scraper

```python
from pyhemnet import HemnetScraper, HemnetItemType

scraper = HemnetScraper()
```

#### Get Summary Statistics

Get counts of properties for sale and sold:

```python
# Get summary for a specific location
listing_count, sold_count = scraper.get_summary(location_id="17744")
print(f"For sale: {listing_count}, Sold: {sold_count}")

# Filter by property types
listing_count, sold_count = scraper.get_summary(
    location_id="17744",
    item_types=[HemnetItemType.VILLA]
)
```

#### Get Sold Properties

Retrieve detailed information about sold properties:

```python
homes = scraper.get_sold(
    location_id="17744",
    item_types=[HemnetItemType.VILLA, HemnetItemType.RADHUS]
)

for home in homes:
    print(f"Address: {home['address']}")
    print(f"Final price: {home['final_price']} SEK")
    print(f"Asking price: {home['asking_price']} SEK")
    print(f"Living area: {home['living_area']}")
    print(f"Sold date: {home['sold_at']}")
    print("---")
```

#### Get Current Listings

Get properties currently for sale:

```python
listings = scraper.get_listings(
    location_id="17744",
    item_types=[HemnetItemType.BOSTADSRATT]
)

for listing in listings:
    print(f"Address: {listing['address']}")
    print(f"Price: {listing['asking_price']} SEK")
    print(f"Published: {listing['published_at']}")
```

#### Property Types

Use the `HemnetItemType` enum or strings:

```python
# Using enum (recommended)
item_types = [HemnetItemType.VILLA, HemnetItemType.RADHUS]

# Using strings
item_types = ["villa", "radhus"]
```

Available types:
- `VILLA` - Detached houses
- `RADHUS` - Townhouses
- `BOSTADSRATT` - Condominiums
- `FRITIDSHUS` - Vacation homes
- `TOMT` - Land plots
- `GARD` - Farms
- `OTHER` - Other property types

### Qasa API

#### Initialize the Scraper

```python
from pyhemnet import QasaScraper

scraper = QasaScraper()
```

#### Search for Rental Homes

Search for available rental properties with various filters:

```python
homes = scraper.get_homes(
    area_identifier="se/helsingborg",  # Single location
    home_types=["apartment", "house", "terrace_house"],
    shared=False,  # Non-shared only
    furnished=None,  # Both furnished and unfurnished
    min_monthly_cost=5000,
    max_monthly_cost=20000,
    pets_allowed=True,
    smoking_allowed=False
)

for home in homes:
    print(f"ID: {home['id']}")
    print(f"Title: {home['title']}")
    print(f"Rent: {home['rent']} {home['currency']}")
    print(f"Location: {home['locality']}, {home['route']}")
    print(f"Rooms: {home['rooms']}, Size: {home['square_meters']} m²")
    print(f"Available from: {home['start_date']}")
    print("---")
```

#### Search Multiple Locations

```python
# Search in multiple areas
homes = scraper.get_homes(
    area_identifier=["se/stockholm", "se/gothenburg", "se/malmo"],
    min_monthly_cost=8000,
    max_monthly_cost=15000
)
```

#### Get Detailed Home Information

Get comprehensive details for a specific rental property:

```python
details = scraper.get_home_details(home_id="12345")

# Basic information
print(f"Title: {details['title']}")
print(f"Rent: {details['rent']} {details['currency']}")
print(f"Rooms: {details['roomCount']}")
print(f"Size: {details['squareMeters']} m²")
print(f"Description: {details['description']}")

# Location details
location = details['location']
print(f"Address: {location['route']} {location['streetNumber']}")
print(f"City: {location['locality']}")
print(f"Coordinates: {location['latitude']}, {location['longitude']}")

# Landlord information
landlord = details['landlord']
print(f"Landlord: {landlord.get('firstName', landlord.get('companyName'))}")
print(f"Response rate: {landlord.get('landlordApplicationResponseRate')}%")

# Rental period
duration = details['duration']
print(f"Start date: {duration['startOptimal']}")
print(f"End date: {duration['endOptimal']}")
print(f"Extension possible: {duration['possibilityOfExtension']}")

# Additional costs
electricity = details['electricityFee']
heating = details['heatingFee']
water = details['waterFee']
print(f"Electricity: {electricity.get('monthlyFee')} SEK/month ({electricity.get('paymentPlan')})")
```

#### Available Home Types

Qasa supports various home types:
- `apartment` - Apartments
- `house` - Houses
- `terrace_house` - Terrace houses
- `duplex` - Duplex apartments
- `studio` - Studio apartments
- `room` - Single rooms

#### Category Filters

Filter by specific categories:
- `firsthand` - First-hand contracts
- `studentHome` - Student housing
- `seniorHome` - Senior housing
- `corporateHome` - Corporate housing

```python
# Example: Search for student housing
homes = scraper.get_homes(
    area_identifier="se/lund",
    category="studentHome",
    max_monthly_cost=8000
)
```

## Data Structure

### Hemnet Data

#### Sold Property Data

Each sold property dictionary contains:

```python
{
    'id': str,              # Hemnet ID
    'listing_id': str,      # Listing identifier
    'address': str,         # Street address
    'location': str,        # Location description
    'housing_type': str,    # Type of housing (Villa, Radhus, etc.)
    'rooms': int,           # Number of rooms
    'living_area': str,     # Living area with units
    'land_area': str,       # Land area with units
    'asking_price': int,    # Initial asking price in SEK
    'final_price': int,     # Final sold price in SEK
    'price_change': str,    # Price change information
    'sold_at': str,         # Sale date (YYYY-MM-DD format)
    'broker': str,          # Broker agency name
    'labels': list,         # List of property labels/tags
}
```

#### Current Listing Data

Each listing dictionary contains:

```python
{
    'id': str,                      # Hemnet ID
    'address': str,                 # Street address
    'location': str,                # Location description
    'housing_type': str,            # Type of housing
    'rooms': int,                   # Number of rooms
    'living_area': str,             # Living area with units
    'land_area': str,               # Land area with units
    'asking_price': int,            # Asking price in SEK
    'published_at': str,            # Publication date (YYYY-MM-DD)
    'removed_before_showing': bool, # Removed before showing
    'new_construction': bool,       # New construction flag
    'broker_name': str,             # Broker name
    'broker_agent': str,            # Broker agency name
    'labels': list,                 # List of property labels/tags
    'description': str,             # Property description
}
```

### Qasa Data

#### Rental Home List Data

Each rental home in the list contains:

```python
{
    'id': str,              # Qasa home ID
    'title': str,           # Property title
    'rent': int,            # Monthly rent
    'currency': str,        # Currency (e.g., 'SEK')
    'rooms': int,           # Number of rooms
    'square_meters': int,   # Size in square meters
    'start_date': date,     # Available from date (date object or None)
    'locality': str,        # City/locality
    'route': str,           # Street name
    'street_number': str,   # Street number
    'country_code': str,    # Country code (e.g., 'SE')
}
```

#### Detailed Rental Home Data

Detailed home information includes:

```python
{
    # Basic information
    'id': str,
    'title': str,
    'rent': int,
    'roomCount': int,
    'squareMeters': int,
    'currency': str,
    'description': str,
    'shared': bool,
    'firsthand': bool,
    'studentHome': bool,
    'seniorHome': bool,
    'corporateHome': bool,

    # Property details
    'floor': int,
    'buildingFloors': int,
    'bedCount': int,
    'bedroomCount': int,
    'hasKitchen': bool,
    'toiletCount': int,
    'houseRules': str,
    'housingAssociation': str,
    'buildYear': int,
    'energyClass': str,
    'kitchenRenovationYear': int,
    'bathroomRenovationYear': int,

    # Location (nested dict)
    'location': {
        'locality': str,
        'latitude': float,
        'longitude': float,
        'route': str,
        'streetNumber': str,
        'countryCode': str,
        'postalCode': str,
        'pointsOfInterest': {
            'nodes': [
                {
                    'category': str,
                    'distance': int,
                    'name': str,
                    'latitude': float,
                    'longitude': float
                }
            ]
        }
    },

    # Landlord (nested dict)
    'landlord': {
        'uid': str,
        'firstName': str,
        'companyName': str,
        'premium': bool,
        'professional': bool,
        'landlordApplicationResponseRate': int,
        'landlordApplicationResponseTimeHours': int,
        'bio': {'intro': str},
        'createdAt': str,
        'seenAt': str
    },

    # Duration (nested dict)
    'duration': {
        'startOptimal': str,
        'endOptimal': str,
        'startAsap': bool,
        'endUfn': bool,
        'possibilityOfExtension': bool
    },

    # Fees (nested dicts)
    'electricityFee': {
        'paymentPlan': str,
        'monthlyFee': int
    },
    'heatingFee': {
        'paymentPlan': str,
        'monthlyFee': int
    },
    'waterFee': {
        'paymentPlan': str,
        'monthlyFee': int
    },
    'tenantBaseFee': int,

    # Requirements (nested dict)
    'rentalRequirement': {
        'approvedCreditCheck': bool,
        'verifiedIncome': bool,
        'rentMultiplier': int,
        'verifiedIdNumber': bool
    },

    # Additional info
    'rentalType': str,
    'status': str,
    'publishedAt': str,
    'tenantCount': int,
    'minTenantCount': int,
    'maxTenantCount': int,
    'tenureType': str
}
```

## Finding Location IDs

To find Hemnet location IDs:

1. Go to [Hemnet.se](https://www.hemnet.se)
2. Search for your desired location
3. Look at the URL - it contains `location_ids[]=XXXXX`
4. Use that ID in your code

Example: For Stockholm `https://www.hemnet.se/bostader?location_ids[]=17744`, use `location_id="17744"`

## Finding Qasa Area Identifiers

To find Qasa area identifiers:

1. Go to [Qasa.se](https://www.qasa.se)
2. Search for your desired location
3. Look at the URL - it contains the area identifier like `se/city-name`
4. Use that identifier in your code

Example: For Helsingborg `https://www.qasa.se/rent/se/helsingborg`, use `area_identifier="se/helsingborg"`

Common area identifiers:
- Stockholm: `"se/stockholm"`
- Gothenburg: `"se/gothenburg"`
- Malmö: `"se/malmo"`
- Uppsala: `"se/uppsala"`
- Lund: `"se/lund"`
- Helsingborg: `"se/helsingborg"`

## Requirements

- Python 3.10+
- cloudscraper >= 1.2.71
- beautifulsoup4 >= 4.12.0
- requests >= 2.31.0

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This package is created for exploring python and web technologies and learning purposes only. It is **not intended for production use** or commercial applications.

- This is an unofficial package and is not affiliated with or endorsed by Hemnet AB or Qasa AB
- Always respect website terms of service and robots.txt directives
- Web scraping may be subject to legal restrictions in your jurisdiction
- Use at your own risk and responsibility
