"""The module container the spider that does the scraping of auction lots."""
import time
import typing

import scrapy
from scrapy.http import Request, Response
from scrapy.loader import ItemLoader
from scrapy.utils.project import get_project_settings
from scrapy_splash import SplashRequest, SplashResponse

from scraper.items import LotItem

SETTINGS = get_project_settings()
PAGE_LOAD_WAIT_TIME = SETTINGS.get("SPLASH_PAGE_LOAD_WAIT_TIME", 5)

LUA_GO_TO_PAGE = """
    -- Lua function that calls jQuery func to go to another page
    function main(splash, args)
        assert(splash:go(args.url))
        -- wait for the page to load JS
        assert(splash:wait({page_load_wait_time}))
        assert(splash:runjs('$.paginationUtils.goPage({page_num})'))
        -- set page load time
        assert(splash:wait({page_load_wait_time}))
        return {{
            html = splash:html(),
            png = splash:png(),
            har = splash:har(),
        }}
    end
"""


class LotSpider(scrapy.Spider):
    """Spider that crawls auction pages and collects info on lots."""

    name = "lot_spider"
    allowed_domains = ["k-auction.com"]
    # specify the 'www' subdomain to avoid login prompts
    start_urls = ["https://www.k-auction.com"]

    def parse(self, response: Response) -> SplashRequest:
        """Find the current auction links on the landing page and start scraping."""

        try:
            if self.auction_urls:
                urls = self.auction_urls.split(",")
        except AttributeError:
            # current auctions urls
            urls = set(
                response.css("[href]::attr(href)").re(
                    "/Auction/(?:Major|Weekly|Premium)/\d+"
                )
            )

        self.logger.info(f"URLs that will be crawled: {urls}.")
        for url in urls:
            time.sleep(2)  # disable simultaneous request dispatch
            *_, auction, auction_num = url.split("/")
            yield SplashRequest(
                url=response.urljoin(url),
                args={"wait": PAGE_LOAD_WAIT_TIME},
                callback=self.parse_auction_page,
                meta={"auction": auction, "auction_num": auction_num},
            )

    def parse_auction_page(
        self, response: SplashResponse
    ) -> typing.Union[SplashRequest, LotItem]:
        """Parse auction page to get info on lots."""

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

        active_page_num = response.css(".paginate_button.active a::text").get()
        next_page_button_link = response.css(
            ".paginate_button.active + li a[href]"
        ).get()
        if next_page_button_link:
            next_page_num = int(active_page_num) + 1
            self.logger.info(
                f"\n\nFinished crawling page {active_page_num} - going to the next page...\n"
            )
            yield SplashRequest(
                response.url,
                self.parse_auction_page,
                endpoint="execute",
                args={
                    "lua_source": LUA_GO_TO_PAGE.format(
                        page_load_wait_time=PAGE_LOAD_WAIT_TIME,
                        page_num=next_page_num,
                    ),
                },
                meta={"auction": auction, "auction_num": auction_num},
            )
