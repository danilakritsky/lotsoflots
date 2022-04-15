"""The module container the spide that does the scraping of auction lots."""
import copy
import pdb
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
            *_, auction, auction_num = url.split("/")
            yield response.follow(
                url=url,
                callback=self.parse_auction_page,
                meta={"auction": auction, "auction_num": auction_num},
            )

    def parse_auction_page(self, response: Response) -> typing.Union[Request, LotItem]:
        """Parse auction page to get info on lots."""
        lots = response.css(".listInner")

        for lot in lots:
            # create new loader for every item here
            # since passing loader by meta from parse() raises the "Can't picke Selector objects" error
            # @ https://stackoverflow.com/questions/49659261/scrapy-cloud-spider-requests-fail-with-generatorexit
            loader = ItemLoader(item=LotItem(), selector=lot)
            loader.add_value("auction", response.meta["auction"])
            loader.add_value("auction_num", response.meta["auction_num"])
            loader.add_css("lot_num", ".listLot::text")
            loader.add_css("image_url", "[src]::attr(src)")

            lot_url = lot.css("[data-link]::attr(data-link)").get()
            yield response.follow(
                url=lot_url, callback=self.parse_lot_page, meta={"loader": loader}
            )

    def parse_lot_page(self, response: Response) -> LotItem:
        """Extract lot information from its page."""
        loader = response.meta["loader"]
        loader.selector = response.body
        return loader.load_item()


def save_result(response: Response, filename="lots_scraped.html") -> None:
    with open(filename, "a+") as f:
        f.write(response)
    print(f"Data saved to {filename}.")
