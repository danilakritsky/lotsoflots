"""This module contains the model for scraped lot info."""

import scrapy
from itemloaders.processors import Compose, Identity, Join, TakeFirst
from scrapy import Field


def take_first(list_of_str: list[str]) -> str:
    """Get the first element from a list of strings."""
    return list_of_str[0]


class LotItem(scrapy.Item):
    """Item representing an auction lot."""

    auc_kind = Field(
        input_processor=Compose(take_first, int), output_processor=TakeFirst()
    )
    auc_num = Field(output_processor=TakeFirst())
    lot_num = Field(output_processor=TakeFirst())
    artist_uid = Field(output_processor=TakeFirst())
    artist_name = Field(output_processor=TakeFirst())
    title = Field(output_processor=TakeFirst())
    size = Field(output_processor=TakeFirst())
    code = Field(output_processor=TakeFirst())
    img_file_name = Field(output_processor=TakeFirst())
    img_file_url = Field(output_processor=TakeFirst())
