"""The module container the spide that does the scraping of auction lots."""
import typing

import scrapy
from scrapy.http import Request, Response
from scrapy.loader import ItemLoader

from scraper.items import LotItem


class LotSpider(scrapy.Spider):
    """Crawl auction pages and collect info on lots."""

    name = "lot_spider"
    allowed_domains = ["k-auction.com"]
    # specify www to avoid redirects to login
    start_urls = ["https://www.k-auction.com"]

    def parse(self, response: Response) -> Request:
        """Find the current auction links on the landing page and start scraping."""

        current_auctions_urls = set(
            response.css("[href]::attr(href)").re(
                "/Auction/(?:Major|Weekly|Premium)/\d+"
            )
        )

        self.logger.info(f"Found current auction urls: {current_auctions_urls}")
        for url in current_auctions_urls:
            yield response.follow(url=url, callback=self.parse_auction_page)

    def parse_auction_page(self, response: Response) -> typing.Union[Request, LotItem]:
        """Parse auction page to get info on lots."""
        loader = ItemLoader(item=LotItem(), selector=response)
        loader.add_css("auction", ".subtop-desc h1::text")
        yield loader.load_item()
