"""This module defines a pipeline that saves scraped data to a database."""

from scrapy.exceptions import DropItem
from sqlalchemy.orm import sessionmaker

from scraper.models import Lot, create_lot_table, db_connect
from scraper.spiders.lot_spider import LotSpider

from .items import LotItem


class PostgresPipeline:
    """Pipeline that saves scraped item to a postgres instance."""

    def __init__(self):
        """Initialize database connection and create table."""
        engine = db_connect()
        create_lot_table(engine)
        self.session = sessionmaker(bind=engine)

    def process_item(self, item: LotItem, spider: LotSpider) -> LotItem | None:
        """Process and save the item to the database."""
        session = self.session()
        lot_exists = session.query(Lot).filter_by(**item)
        # drop item if exists
        if lot_exists.first():
            session.close()
            raise DropItem(f"Duplicate item ignored.\n")
        else:
            lot = Lot(**item)
            spider.logger.info("Saving item.")
            try:
                session.add(lot)
                session.commit()
                spider.logger.info("Item saved.\n")
            except:
                session.rollback()
                raise
            finally:
                session.close()

            return item
