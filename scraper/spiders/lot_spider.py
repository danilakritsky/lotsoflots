"""The module container the spide that does the scraping of auction lots."""
import copy
import pdb
import typing

import scrapy
from scrapy.http import Request, Response
from scrapy.loader import ItemLoader
from scrapy_splash import SplashRequest

from scraper.items import LotItem


class LotSpider(scrapy.Spider):
    """Crawl auction pages and collect info on lots."""

    name = "lot_spider"
    allowed_domains = ["k-auction.com"]
    # specify www to avoid redirects to login
    start_urls = ["https://www.k-auction.com"]

    def parse(self, response: Response) -> SplashRequest:
        """Find the current auction links on the landing page and start scraping."""

        current_auctions_urls = set(
            response.css("[href]::attr(href)").re(
                #"/Auction/(?:Major|Weekly|Premium)/\d+"
                "/Auction/(?:Major)/\d+"
            )
        )

        self.logger.info(f"Found current auction urls: {current_auctions_urls}")
        for url in current_auctions_urls:
            *_, auction, auction_num = url.split("/")
            yield SplashRequest(
                url=response.urljoin(url),
                callback=self.parse_auction_page,
                meta={"auction": auction, "auction_num": auction_num},
            )

    def parse_auction_page(self, response: Response) -> typing.Union[Request, LotItem]:
        """Parse auction page to get info on lots."""

        lots = response.css(".card.artwork")
        for lot in lots:
            # create new loader for every item here
            # since passing loader by meta from parse() raises the "Can't picke Selector objects" error
            # @ https://stackoverflow.com/questions/49659261/scrapy-cloud-spider-requests-fail-with-generatorexit
            loader = ItemLoader(item=LotItem(), selector=lot)
            loader.add_value("auction", auction := response.meta["auction"])
            loader.add_value("auction_num", auction_num := response.meta["auction_num"])
            loader.add_css("lot_num", ".lot::text")
            loader.add_css("lot_artist", ".card-title::text")
            loader.add_css("lot_title", ".card-subtitle::text")
            loader.add_css("lot_dimensions", "span.text-truncate::text")
            loader.add_css("lot_image_url", "[src]::attr(src)")
            yield loader.load_item()
        
        lua_func_def_go_to_next_page = """
            function main(splash, args)
                assert(splash:go(args.url))
                assert(splash:wait(0.5))
                assert(splash:runjs('document.getElementsByClassName("next")[0].children[0].click()'))
                    assert(splash:wait(10))
                return {
                    html = splash:html(),
                    png = splash:png(),
                    har = splash:har(),
                }
            end
        """

        # NOTE: Please click on the next page to view the new category.
        active_page =  response.css('.paginate_button.active a::text').get()
        print('!!!!!!!!! active page\n', active_page)
        next_page_disabled = response.css('.next.disabled').get()
        if not next_page_disabled:
            yield SplashRequest(
                response.url,
                self.parse_auction_page, 
                endpoint='execute',
                args={
                    'lua_source': lua_func_def_go_to_next_page,
                },
                cache_args=['lua_source'],
                dont_filter=True,
                meta={"auction": auction, "auction_num": auction_num},)   


    def save_result(self, response: Response, filename="lots_scraped.html") -> None:
        print(response)
        active_page =  response.css('.paginate_button.active a::text').get()
        print('!!!!!!!!! active page\n', active_page)
        with open(filename, "wb+") as f:
            f.write(response.body)
        print(f"Data saved to {filename}.")
