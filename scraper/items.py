"""This module contains the model for scraped lot info."""

import scrapy
from itemloaders.processors import Compose, Identity, Join, TakeFirst
from scrapy import Field


def take_first(list_of_str: list[str]) -> str:
    """Get the first element from a list of strings."""
    return list_of_str[0]


class LotItem(scrapy.Item):
    auction = Field(output_processor=TakeFirst())
    auction_num = Field(
        input_processor=Compose(take_first, int), output_processor=TakeFirst()
    )
    lot_num = Field(
        input_processor=Compose(take_first, lambda x: x.strip("Lot"), int),
        output_processor=TakeFirst(),
    )
    lot_artist = Field(output_processor=TakeFirst())
    lot_title = Field(output_processor=TakeFirst())
    lot_dimensions = Field(
        input_processor=Compose(take_first, lambda x: x.split("|")[0].strip()),
        output_processor=TakeFirst(),
    )
    lot_image_url = Field(output_processor=TakeFirst())
