"""The module container the spider that does the scraping of auction lots."""
import json
import time
import typing

import scrapy
from scraper.items import LotItem
from scrapy.http import Request, Response
from scrapy.loader import ItemLoader
from scrapy.utils.project import get_project_settings


class LotSpider(scrapy.Spider):
    """Spider that crawls auction pages and collects info on lots."""

    name = "lot_spider"
    allowed_domains = ["k-auction.com"]
    # specify the 'www' subdomain to avoid login prompts
    start_urls = ["https://www.k-auction.com"]
    auc_kinds = {"Major": 1, "Premium": 2, "Weekly": 4}

    def parse(self, response: Response) -> Request:
        """Find the current auction links on the landing page and start scraping."""

        try:
            if self.auction_urls:
                urls = self.auction_urls.split(",")
        except AttributeError:
            # current auctions urls
            urls = set(
                response.xpath("//@href").re(
                    "/Auction/(?:Major|Premium|Weekly)/\d+",
                    # "/Auction/(?:Major)/\d+"
                )
            )

        for url in urls:
            *_, auc_name, auc_num = url.split("/")
            yield Request(
                url=response.urljoin(url),
                method="GET",
                callback=self.parse_img_urls,
                meta={
                    "auc_name": auc_name,
                    "auc_num": auc_num,
                    "auc_kind": self.auc_kinds[auc_name],
                },
            )

    def parse_img_urls(self, response: Response) -> Request:
        """Extract image urls."""
        (img_file_parent_url,) = set(
            response.xpath('//*[@class="listImg"]//@src').re("(.*/)(?!.*/.*)")
        )
        meta = response.meta

        payload = {
            "page_size": "10",
            "page_type": "P",
            "auc_kind": (auc_kind := meta["auc_kind"]),
            "auc_num": (auc_num := meta["auc_num"]),
            "page": 1,
        }

        yield Request(
            url=f"{self.start_urls[0]}/api/Auction/{auc_kind}/{auc_num}",
            method="POST",
            headers={
                "Content-type": "application/json",
            },
            body=json.dumps(payload),
            callback=self.parse_auction_page,
            meta={"img_file_parent_url": img_file_parent_url},
        )

    def parse_auction_page(self, response: Response) -> typing.Union[Request, LotItem]:
        """Parse auction page to get info on lots."""

        lots = json.loads(response.text)["data"]

        if lots:
            meta = response.meta
            for lot in lots:
                # skip empty cards
                if artist_uid := lot["artist_uid"]:
                    loader = ItemLoader(item=LotItem(), selector=lot)
                    loader.add_value("auc_kind", lot["auc_kind"])
                    loader.add_value("auc_num", lot["auc_num"])
                    loader.add_value("lot_num", lot["lot_num"])
                    loader.add_value("artist_uid", artist_uid)
                    loader.add_value("artist_name", lot["artist_name"])
                    loader.add_value("title", lot["title"])
                    loader.add_value("size", lot["size"])
                    loader.add_value("code", lot["code"])
                    loader.add_value("img_file_name", lot["img_file_name"])
                    loader.add_value(
                        "img_file_url",
                        meta["img_file_parent_url"] + lot["img_file_name"],
                    )
                    yield loader.load_item()

            payload = json.loads(response.request.body)
            payload |= {"page": payload["page"] + 1}

            yield Request(
                url=response.url,
                method="POST",
                headers={
                    "Content-type": "application/json",
                },
                body=json.dumps(payload),
                callback=self.parse_auction_page,
                meta=meta,
            )
