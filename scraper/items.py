"""This module contains the model for scraped lot info."""

import scrapy
from itemloaders.processors import Compose, Identity, Join, TakeFirst
from scrapy import Field


class LotItem(scrapy.Item):
    auction = Field(output_processor=TakeFirst())
    auction_num = Field(
        input_processor=Compose(lambda x: x[0], int), output_processor=TakeFirst()
    )
    lot_num = Field(
        input_processor=Compose(lambda x: x[0], lambda x: x.strip("LOT"), int),
        output_processor=TakeFirst(),
    )
    image_url = Field(output_processor=TakeFirst())
