"""Hemnet scraper module for property sales data extraction"""

import datetime as dt
import json
import logging
import re

from bs4 import BeautifulSoup
from curl_cffi import requests as curl_requests

from .constants import HEMNET_URLS, HemnetItemType

logger = logging.getLogger(__name__)


class HemnetScraper:
    """Scraper for Hemnet property sales data

    Examples:
        >>> scraper = HemnetScraper()
        >>> listing, sold = scraper.get_summary(location_id="17932")
        >>> homes = scraper.get_sold(
        ...     location_id="17932",
        ...     item_types=[HemnetItemType.VILLA, HemnetItemType.RADHUS]
        ... )

        # With strings
        >>> homes = scraper.get_sold(
        ...     location_id="17932",
        ...     item_types=["villa", "radhus"]
        ... )
    """

    def __init__(self):
        """Initialize the Hemnet scraper"""
        self.scraper = curl_requests.Session(impersonate="chrome")

    def _build_url(
        self,
        url_type: str,
        location_id: str | None = None,
        item_types: list[HemnetItemType | str] | None = None,
        page: int | None = None,
    ) -> str:
        """Build URL dynamically based on type (internal)

        Args:
            url_type: Type of URL to build ('listings' or 'sold')
            location_id: Hemnet location ID (optional)
            item_types: List of property types (optional)
            page: Page number for pagination (optional, starts at 1)

        Returns:
            Constructed URL string

        Raises:
            ValueError: If url_type is invalid
        """
        # Select base URL
        base_url = HEMNET_URLS.get(url_type)
        if base_url is None:
            raise ValueError(
                f"Invalid url_type: {url_type}. Must be 'listings' or 'sold'"
            )

        params = []

        # Add location_id if provided
        if location_id:
            params.append(f"location_ids[]={location_id}")

        # Add item_types if provided
        if item_types:
            item_type_strs = [
                t.value if isinstance(t, HemnetItemType) else t for t in item_types
            ]
            for item_type in item_type_strs:
                params.append(f"item_types[]={item_type}")

        # Add sorting parameters
        if url_type == "listings":
            params.extend(["by=creation", "order=desc"])
        else:  # sold
            params.extend(["by=sale_date", "order=desc"])

        # Add page number if provided
        if page and page > 1:
            params.append(f"page={page}")

        # Build final URL
        if params:
            return f"{base_url}?{'&'.join(params)}"
        return base_url

    def _make_request(self, url: str) -> dict:
        """Fetch and parse data from a Hemnet page (internal)

        Args:
            url: URL to scrape

        Returns:
            Parsed page data

        Raises:
            ValueError: If page data cannot be found or parsed
        """
        response = self.scraper.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        script_tag = soup.find("script", id="__NEXT_DATA__")

        if script_tag and script_tag.string:
            try:
                return json.loads(script_tag.string)
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse JSON data from {url}: {e}")

        page_data = self._extract_rendered_page_data(soup)
        if page_data is not None:
            return page_data

        heading = soup.find("h1")
        heading_text = heading.get_text(" ", strip=True) if heading else ""
        match = re.match(
            r"([\d][\d\s.,\u00a0\u202f]*)\s+(bostäder till salu|sålda bostäder)\b",
            heading_text,
            re.IGNORECASE,
        )
        if match:
            page_type = (
                "listings" if match.group(2).lower() == "bostäder till salu" else "sold"
            )
            return {
                "__hemnet_page_type__": page_type,
                "__hemnet_page_total__": self._extract_int(match.group(1)),
            }
        raise ValueError(f"Could not find page data in page: {url}")

    @staticmethod
    def _extract_rendered_page_data(soup: BeautifulSoup) -> dict | None:
        """Extract search results embedded in a Next.js Flight page."""
        decoder = json.JSONDecoder()
        flight_chunks = []

        for script_tag in soup.find_all("script"):
            script_text = script_tag.string or script_tag.get_text()
            for match in re.finditer(r"self\.__next_f\.push\(\[1,", script_text):
                try:
                    chunk, _ = decoder.raw_decode(script_text, match.end())
                except json.JSONDecodeError:
                    continue
                if isinstance(chunk, str):
                    flight_chunks.append(chunk)

        markers = (
            ("saveSearchTrackingResult", "listings", "ListingResultsCombined"),
            ("searchResult", "sold", "SoldListingResults"),
        )
        for flight_chunk in flight_chunks:
            for key, page_type, typename in markers:
                marker = re.compile(rf'"{re.escape(key)}"\s*:\s*')
                for match in marker.finditer(flight_chunk):
                    try:
                        result, _ = decoder.raw_decode(flight_chunk, match.end())
                    except json.JSONDecodeError:
                        continue
                    if (
                        isinstance(result, dict)
                        and result.get("__typename") == typename
                        and isinstance(result.get("total"), (int, float))
                        and isinstance(result.get("cards"), list)
                    ):
                        return {
                            "__hemnet_page_type__": page_type,
                            "__hemnet_page_total__": int(result["total"]),
                            "__hemnet_cards__": result["cards"],
                        }
        return None

    @staticmethod
    def _extract_int(value: str | None, default: int = 0) -> int:
        """Extract integer from string by removing non-digits (internal helper)"""
        if not value:
            return default
        cleaned = re.sub(r"[^\d]", "", str(value))
        return int(cleaned) if cleaned else default

    @staticmethod
    def _extract_housing_type(data: dict) -> str | None:
        """Extract housing type from housing form data (internal helper)"""
        housing_form = data.get("housingForm")
        return housing_form.get("name") if isinstance(housing_form, dict) else None

    @staticmethod
    def _extract_labels(data: dict) -> list[str]:
        """Extract text labels from label data (internal helper)"""
        return [
            label["text"]
            for label in data.get("labels", [])
            if isinstance(label, dict) and "text" in label
        ]

    @staticmethod
    def _format_timestamp(timestamp: int | None) -> str | None:
        """Format Unix timestamp to YYYY-MM-DD string (internal helper)"""
        if not timestamp:
            return None
        return dt.datetime.fromtimestamp(float(timestamp)).strftime("%Y-%m-%d")

    @staticmethod
    def _clean_area_string(value: str | None) -> str:
        """Clean area string by replacing non-breaking spaces (internal helper)"""
        return re.sub(r"\xa0", " ", str(value or "0"))

    def _parse_summary(self, json_data: dict) -> tuple[int, int]:
        """Extract total listings and sold homes from JSON data (internal)

        Args:
            json_data: Parsed JSON data from page

        Returns:
            Tuple of (total_listings, total_sold)

        Raises:
            ValueError: If required data is missing or invalid
        """
        try:
            summary = json_data["props"]["pageProps"]["__APOLLO_STATE__"]["ROOT_QUERY"]

            # Find listing data
            search_data = summary.get("search")
            listing_data = None
            if isinstance(search_data, dict):
                listing_data = next(
                    (
                        v
                        for k, v in search_data.items()
                        if k.startswith("listings(")
                        and json.loads(k[len("listings(") : -1])
                        .get("search", {})
                        .get("upcoming")
                        != "ONLY"
                    ),
                    None,
                )
            if listing_data is None or "total" not in listing_data:
                raise ValueError("Missing search.listings data")

            # Find sold data
            sold_data = next(
                (v for k, v in summary.items() if k.startswith("searchSales")), None
            )
            if sold_data is None or "total" not in sold_data:
                raise ValueError("Missing searchSales data")

            listing = int(listing_data["total"])
            sold = int(sold_data["total"])

            return listing, sold

        except (KeyError, TypeError) as e:
            raise ValueError(f"Invalid JSON structure: {e}")
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError(f"Non-numeric total value: {e}")
            raise

    def _parse_listing_details(self, json_data: dict) -> list[dict]:
        """Extract details of active listings from JSON data (internal)

        Args:
            json_data: Parsed JSON data from page

        Returns:
            List of dictionaries containing home details

        Raises:
            ValueError: If required data structure is missing or invalid
        """
        if "__hemnet_page_type__" in json_data:
            if json_data["__hemnet_page_type__"] != "listings":
                raise ValueError("Unexpected page type while parsing listings")
            listing_cards = json_data.get("__hemnet_cards__")
            if not isinstance(listing_cards, list):
                raise ValueError("Missing listing cards in rendered page data")
        else:
            try:
                details = json_data["props"]["pageProps"]["__APOLLO_STATE__"]
            except (KeyError, TypeError) as e:
                raise ValueError(f"Invalid JSON structure for details: {e}")

            listing_cards = [
                value
                for key, value in details.items()
                if key.startswith("ListingCard:")
                and isinstance(value, dict)
                and value.get("__typename") == "ListingCard"
            ]

        homes = []
        for data in listing_cards:
            if not isinstance(data, dict) or data.get("__typename") != "ListingCard":
                continue
            try:
                homes.append(
                    {
                        "id": data.get("id"),
                        "address": data.get("streetAddress"),
                        "location": data.get("locationDescription"),
                        "housing_type": self._extract_housing_type(data),
                        "rooms": self._extract_int(data.get("rooms")),
                        "living_area": self._clean_area_string(
                            data.get("livingAndSupplementalAreas")
                        ),
                        "land_area": self._clean_area_string(data.get("landArea")),
                        "asking_price": self._extract_int(data.get("askingPrice")),
                        "published_at": self._format_timestamp(data.get("publishedAt")),
                        "removed_before_showing": data.get("removedBeforeShowing"),
                        "new_construction": data.get("newConstruction"),
                        "broker_name": data.get("brokerName"),
                        "broker_agent": data.get("brokerAgencyName"),
                        "labels": self._extract_labels(data),
                        "description": data.get("description"),
                    }
                )
            except (ValueError, TypeError, AttributeError) as e:
                # Skip individual listings with bad data rather than failing entire parse
                logger.debug(f"Skipping listing {data.get('id', 'unknown')}: {e}")
                continue

        return homes

    def _parse_sold_details(self, json_data: dict) -> list[dict]:
        """Extract details of sold homes from JSON data (internal)

        Args:
            json_data: Parsed JSON data from page

        Returns:
            List of dictionaries containing home details

        Raises:
            ValueError: If required data structure is missing or invalid
        """
        if "__hemnet_page_type__" in json_data:
            if json_data["__hemnet_page_type__"] != "sold":
                raise ValueError("Unexpected page type while parsing sold homes")
            sale_cards = json_data.get("__hemnet_cards__")
            if not isinstance(sale_cards, list):
                raise ValueError("Missing sold cards in rendered page data")
        else:
            try:
                details = json_data["props"]["pageProps"]["__APOLLO_STATE__"]
            except (KeyError, TypeError) as e:
                raise ValueError(f"Invalid JSON structure for details: {e}")

            sale_cards = [
                value
                for key, value in details.items()
                if key.startswith("SaleCard:")
                and isinstance(value, dict)
                and value.get("__typename") == "SaleCard"
            ]

        homes = []
        for data in sale_cards:
            if not isinstance(data, dict) or data.get("__typename") != "SaleCard":
                continue
            try:
                homes.append(
                    {
                        "id": data.get("id"),
                        "listing_id": data.get("listingId"),
                        "address": data.get("streetAddress"),
                        "location": data.get("locationDescription"),
                        "housing_type": self._extract_housing_type(data),
                        "rooms": self._extract_int(data.get("rooms")),
                        "living_area": self._clean_area_string(data.get("livingArea")),
                        "land_area": self._clean_area_string(data.get("landArea")),
                        "asking_price": self._extract_int(data.get("askingPrice")),
                        "final_price": self._extract_int(data.get("finalPrice")),
                        "price_change": self._clean_area_string(
                            data.get("priceChange")
                        ),
                        "sold_at": self._format_timestamp(data.get("soldAt")),
                        "broker": data.get("brokerAgencyName"),
                        "labels": self._extract_labels(data),
                    }
                )
            except (ValueError, TypeError, AttributeError) as e:
                # Skip individual listings with bad data rather than failing entire parse
                logger.debug(f"Skipping sold home {data.get('id', 'unknown')}: {e}")
                continue

        return homes

    def get_summary(
        self,
        location_id: str | None = None,
        item_types: list[HemnetItemType | str] | None = None,
    ) -> tuple[int, int]:
        """Get summary statistics for all properties

        Args:
            location_id: Hemnet location ID (optional)
            item_types: List of property types (optional)

        Returns:
            Tuple of (total_listings, total_sold)

        Raises:
            ValueError: If the page structure is invalid or data cannot be parsed
            requests.exceptions.HTTPError: If the HTTP request fails
        """
        try:
            url = self._build_url("listings", location_id, item_types)
            json_data = self._make_request(url)
            if "__hemnet_page_type__" in json_data:
                if json_data["__hemnet_page_type__"] != "listings":
                    raise ValueError("Unexpected page type while reading listing total")
                sold_url = self._build_url("sold", location_id, item_types)
                sold_data = self._make_request(sold_url)
                if sold_data.get("__hemnet_page_type__") != "sold":
                    raise ValueError("Could not read sold total from Hemnet page")
                return (
                    json_data["__hemnet_page_total__"],
                    sold_data["__hemnet_page_total__"],
                )
            listing, sold = self._parse_summary(json_data)
            return listing, sold
        except ValueError as e:
            raise ValueError(f"Failed to get summary statistics: {e}")

    def get_listings(
        self,
        location_id: str | None = None,
        item_types: list[HemnetItemType | str] | None = None,
        page: int | None = None,
    ) -> list[dict]:
        """Get detailed listings for properties currently for sale

        Args:
            location_id: Hemnet location ID (optional)
            item_types: List of property types (optional)
        Returns:
            List of dictionaries containing property details
        Raises:
            ValueError: If the page structure is invalid or data cannot be parsed
            requests.exceptions.HTTPError: If the HTTP request fails
        """
        try:
            url = self._build_url("listings", location_id, item_types, page)
            json_data = self._make_request(url)
            listings = self._parse_listing_details(json_data)
            return listings
        except ValueError as e:
            raise ValueError(f"Failed to get property listings: {e}")

    def get_sold(
        self,
        location_id: str | None = None,
        item_types: list[HemnetItemType | str] | None = None,
        page: int | None = None,
    ) -> list[dict]:
        """Get detailed listings for sold homes

        Args:
            location_id: Hemnet location ID (optional)
            item_types: List of property types (optional)

        Returns:
            List of dictionaries containing sold home details, where each dict has:
                - id: Hemnet ID
                - listing_id: Listing identifier
                - address: Street address
                - location: Location description
                - housing_type: Type of housing (villa, apartment, etc.)
                - rooms: Number of rooms
                - living_area: Living area with units
                - land_area: Land area with units
                - asking_price: Initial asking price (int)
                - final_price: Final sold price (int)
                - price_change: Price change information
                - sold_at: Sale date (YYYY-MM-DD format or None)
                - broker: Broker agency name
                - labels: List of property labels/tags

        Raises:
            ValueError: If the page structure is invalid or data cannot be parsed
            requests.exceptions.HTTPError: If the HTTP request fails
        """
        try:
            url = self._build_url("sold", location_id, item_types, page)
            json_data = self._make_request(url)
            homes = self._parse_sold_details(json_data)
            return homes
        except ValueError as e:
            raise ValueError(f"Failed to get sold homes listings: {e}")
