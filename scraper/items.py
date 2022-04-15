"""This module contains the model for scraped lot info."""

import scrapy
from itemloaders.processors import Identity, Join, TakeFirst
from scrapy import Field


class LotItem(scrapy.Item):
    auction = Field()
