"""Tests for Hemnet scraper"""

from unittest.mock import patch

import pytest

from pyhemnet import HemnetItemType, HemnetScraper


@pytest.fixture
def scraper():
    """Create a HemnetScraper instance for testing"""
    return HemnetScraper()


@pytest.fixture
def mock_summary_json():
    """Mock JSON data for summary endpoint"""
    return {
        "props": {
            "pageProps": {
                "__APOLLO_STATE__": {
                    "ROOT_QUERY": {
                        "search": {
                            "listings({})": {
                                "total": 150,
                            },
                        },
                        "searchSales({})": {
                            "total": 75,
                        },
                    }
                }
            }
        }
    }


@pytest.fixture
def mock_sold_details_json():
    """Mock JSON data for sold properties endpoint"""
    return {
        "props": {
            "pageProps": {
                "__APOLLO_STATE__": {
                    "SaleCard:123": {
                        "__typename": "SaleCard",
                        "id": "123",
                        "listingId": "L123",
                        "streetAddress": "Test Street 1",
                        "locationDescription": "Stockholm",
                        "housingForm": {"name": "Villa"},
                        "rooms": "5",
                        "livingArea": "150 m²",
                        "landArea": "800 m²",
                        "askingPrice": "5 000 000 kr",
                        "finalPrice": "5 200 000 kr",
                        "priceChange": "+200 000 kr",
                        "soldAt": 1704931200,  # 2024-01-11
                        "brokerAgencyName": "Test Broker",
                        "labels": [{"text": "New"}, {"text": "Popular"}],
                    },
                    "SaleCard:456": {
                        "__typename": "SaleCard",
                        "id": "456",
                        "listingId": "L456",
                        "streetAddress": "Test Street 2",
                        "locationDescription": "Gothenburg",
                        "housingForm": {"name": "Radhus"},
                        "rooms": "3",
                        "livingArea": "100 m²",
                        "landArea": "200 m²",
                        "askingPrice": "3 500 000 kr",
                        "finalPrice": "3 400 000 kr",
                        "priceChange": "-100 000 kr",
                        "soldAt": 1704844800,  # 2024-01-10
                        "brokerAgencyName": "Another Broker",
                        "labels": [],
                    },
                }
            }
        }
    }


@pytest.fixture
def mock_listing_details_json():
    """Mock JSON data for current listings endpoint"""
    return {
        "props": {
            "pageProps": {
                "__APOLLO_STATE__": {
                    "ListingCard:789": {
                        "__typename": "ListingCard",
                        "id": "789",
                        "streetAddress": "New Street 1",
                        "locationDescription": "Malmö",
                        "housingForm": {"name": "Bostadsrätt"},
                        "rooms": "2",
                        "livingAndSupplementalAreas": "65 m²",
                        "landArea": "",
                        "askingPrice": "2 500 000 kr",
                        "publishedAt": 1704758400,  # 2024-01-09
                        "removedBeforeShowing": False,
                        "newConstruction": True,
                        "brokerName": "John Doe",
                        "brokerAgencyName": "Premium Broker",
                        "labels": [{"text": "Nyproduktion"}],
                        "description": "Beautiful apartment",
                    }
                }
            }
        }
    }


class TestHemnetScraper:
    """Test HemnetScraper public API"""

    @patch("pyhemnet.hemnet.HemnetScraper._make_request")
    def test_get_summary(self, mock_request, scraper, mock_summary_json):
        """Test get_summary method"""
        mock_request.return_value = mock_summary_json

        listing, sold = scraper.get_summary(location_id="17744")

        assert listing == 150
        assert sold == 75
        mock_request.assert_called_once()

    @patch("pyhemnet.hemnet.HemnetScraper._make_request")
    def test_get_summary_with_filters(self, mock_request, scraper, mock_summary_json):
        """Test get_summary with location and item type filters"""
        mock_request.return_value = mock_summary_json

        listing, sold = scraper.get_summary(
            location_id="17744",
            item_types=[HemnetItemType.VILLA, HemnetItemType.RADHUS],
        )

        assert listing == 150
        assert sold == 75

    @patch("pyhemnet.hemnet.HemnetScraper._make_request")
    def test_get_sold(self, mock_request, scraper, mock_sold_details_json):
        """Test get_sold method returns properly parsed home data"""
        mock_request.return_value = mock_sold_details_json

        homes = scraper.get_sold(location_id="17744", item_types=[HemnetItemType.VILLA])

        assert len(homes) == 2

        # Verify first home
        assert homes[0]["address"] == "Test Street 1"
        assert homes[0]["final_price"] == 5200000
        assert homes[0]["asking_price"] == 5000000
        assert homes[0]["housing_type"] == "Villa"
        assert homes[0]["rooms"] == 5
        assert homes[0]["labels"] == ["New", "Popular"]
        assert homes[0]["sold_at"] == "2024-01-11"

        # Verify second home has different data
        assert homes[1]["address"] == "Test Street 2"
        assert homes[1]["housing_type"] == "Radhus"

    @patch("pyhemnet.hemnet.HemnetScraper._make_request")
    def test_get_listings(self, mock_request, scraper, mock_listing_details_json):
        """Test get_listings method returns current property listings"""
        mock_request.return_value = mock_listing_details_json

        listings = scraper.get_listings(location_id="17744", item_types=["bostadsratt"])

        assert len(listings) == 1
        assert listings[0]["address"] == "New Street 1"
        assert listings[0]["asking_price"] == 2500000
        assert listings[0]["housing_type"] == "Bostadsrätt"
        assert listings[0]["new_construction"] is True
        assert listings[0]["description"] == "Beautiful apartment"
        assert listings[0]["published_at"] == "2024-01-09"

    @patch("pyhemnet.hemnet.HemnetScraper._make_request")
    def test_error_handling_invalid_json(self, mock_request, scraper):
        """Test that invalid JSON structure raises appropriate error"""
        mock_request.return_value = {"props": {}}

        with pytest.raises(ValueError, match="Invalid JSON structure"):
            scraper.get_summary()

    @patch("pyhemnet.hemnet.HemnetScraper._make_request")
    def test_error_handling_missing_data(self, mock_request, scraper):
        """Test error handling when required data is missing"""
        mock_request.return_value = {
            "props": {"pageProps": {"__APOLLO_STATE__": {"ROOT_QUERY": {}}}}
        }

        with pytest.raises(ValueError, match="Missing search.listings data"):
            scraper.get_summary()
