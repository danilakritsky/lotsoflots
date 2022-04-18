lotsoflots
==========

A simple dockerized scraping project that gathers data on auction lots from [K Auction](https://www.k-auction.com/).

## Project architecture
**lotsoflots**'s workflow is managed by 3 separate services as defined in `docker-compose.yml`:
1. ***scraper*** - `scrapy` project containing `LotSpider` that does the crawling and saves crawled data

2. ***splash*** - a [Splash](https://github.com/scrapinghub/splash) web server utilized by `LotSpider` to render pages' JavaScript

3. ***postgres*** - an instance of PostgreSQL database used to store the scraped items. Data persists across container sessions by using mapped volume inside the project's directory.

## Deployment
**`docker` and `docker-compose` must be available on your system.**  
Clone the project and `cd` into it:
> `git clone https://github.com/danilakritsky/lotsoflots`
>
> `cd lotsoflots`
>
Start containers in detached mode:
> `docker-compose up -d`

## Example usage
### Dispatching spiders from the **scraper** container 
First, login in into the `scraper` container by running:
> `docker exec -it scraper sh`  
>
Then run the following command:
>`scrapy crawl lot_spider`
>
By default `lot_spider` will crawl **all active** auctions: *Major*, *Premium* and *Weekly*.  
You can scrape specific active auction or the results of a closed one by providing the auction's url to the spider. Example:
> `scrapy crawl lot_spider -a auction_urls=https://www.k-auction.com/Auction/Major/149`
>
To scrape *multiple auctions* pass a comma delimited list:
> `scrapy crawl lot_spider -a auction_urls=https://www.k-auction.com/Auction/Major/149,https://www.k-auction.com/Auction/Premium/143`
>

### Dispatching spiders from localhost
To scrape accounts *without logging* into the `scraper` container use:
>`docker exec scraper  sh -c 'scrapy crawl lot_spider -a auction_urls=https://www.k-auction.com/Auction/Major/149,https://www.k-auction.com/Auction/Premium/143'`
>

### Examine stored data
To view data stored in **postgres**, first login to the container:  
> `docker exec -it postgres sh`  
>
In container run the following command to open postgres shell:
> `psql -U postgres`
>
When in postgres shell run the 2 following commands to view stored items:
> `\c lotsoflots`  
>  `SELECT * FROM lots;`

### Stopping services
To stop all containers run:
> `docker-compose down`
>

### Troubleshooting
The most common error encountered is the spider failing to follow pagination.  
Most of the time the reason is simple: Splash web server could not render the page's JavaScript content in time for the spider to find the next page button.  
Usually, restarting the `scrapy crawl` command would suffice, but if the problem persists consider increasing the value of `SPLASH_PAGE_LOAD_WAIT_TIME` in the **scraper** service's `settings.py`.  

Another recurring problem is getting *504 Gateway Timeout* errors when making requests to the Splash server - in this case spider will automatically retry the request which works most of the time.  If that fails, rerunning the `scrapy crawl` command should help.
