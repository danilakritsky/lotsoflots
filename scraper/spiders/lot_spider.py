"""The module container the spider that does the scraping of auction lots."""
import typing
from fileinput import filename

import scrapy
from scrapy.http import Request, Response
from scrapy.loader import ItemLoader
from scrapy_splash import SplashRequest

from scraper.items import LotItem

LUA = """
    -- Lua function to press next page button
    function main(splash, args)
        -- assert(splash:go(args.url))
        local previous_response = args.previous_response
        assert(splash:set_content(previous_response, "text/html; charset=utf-8", args.url))
        assert(splash:runjs('document.querySelector(".paginate_button.active + li").querySelector("a").click()'))
        assert(splash:wait(2))
        return {
            html = splash:html(),
            png = splash:png(),
            har = splash:har(),
        }
    end
"""


class LotSpider(scrapy.Spider):
    """Crawl auction pages and collect info on lots."""

    name = "lot_spider"
    allowed_domains = ["k-auction.com"]
    # specify the 'www' subdomain to avoid login prompts
    start_urls = ["https://www.k-auction.com"]

    def parse(self, response: Response) -> SplashRequest:
        """Find the current auction links on the landing page and start scraping."""

        current_auctions_urls = set(
            response.css("[href]::attr(href)").re(
                # "/Auction/(?:Major|Weekly|Premium)/\d+"
                "/Auction/(?:Major)/\d+"
            )
        )

        self.logger.info(f"Found current auction urls: {current_auctions_urls}")
        for url in current_auctions_urls:
            *_, auction, auction_num = url.split("/")
            yield SplashRequest(
                url=response.urljoin(url),
                args={"wait": 2},
                callback=self.parse_auction_page,
                meta={"auction": auction, "auction_num": auction_num},
            )

    def parse_auction_page(self, response: Response) -> typing.Union[Request, LotItem]:
        """Parse auction page to get info on lots."""

        active_page = response.css(".paginate_button.active a::text").get()
        next_page_disabled = response.css(".next.disabled").get()

        lots = response.css(".card.artwork")
        for lot in lots:
            # handle empty lot cards
            if lot_num := lot.css(".lot::text").get():
                # create new loader for every item here
                # since passing loader by meta from parse() raises the "Can't picke Selector objects" error
                # @ https://stackoverflow.com/questions/49659261/scrapy-cloud-spider-requests-fail-with-generatorexit
                loader = ItemLoader(item=LotItem(), selector=lot)
                loader.add_value("auction", auction := response.meta["auction"])
                loader.add_value(
                    "auction_num", auction_num := response.meta["auction_num"]
                )
                loader.add_value("lot_num", lot_num)
                loader.add_css("lot_artist", ".card-title::text")
                loader.add_css("lot_title", ".card-subtitle::text")
                loader.add_css("lot_dimensions", "span.text-truncate::text")
                loader.add_css("lot_image_url", "[src]::attr(src)")
                yield loader.load_item()

        if not next_page_disabled:
            yield SplashRequest(
                response.url,
                self.parse_auction_page,
                endpoint="execute",
                args={
                    "wait": 2,
                    "lua_source": LUA,
                    # NOTE: setting previous_response in splash:set_content does not work
                    # possible reason: page depends on external JS, which is not included with the passed content
                    "previous_response": response.text,
                },
                meta={"auction": auction, "auction_num": auction_num},
            )

    def save_result(self, text, filename="lots_scraped.html") -> None:
        with open(filename, "w+") as f:
            f.write(text)
        print(f"Data saved to {filename}.")
