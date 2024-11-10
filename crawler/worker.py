from threading import Thread, Event

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time

from urllib.parse import urlparse

pause_event = Event()
pause_event.set()


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.id = worker_id
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        self.current_domain = self.frontier.get_domain()
        self.frontier.active_workers[self.id] = True
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def run(self):
        while True:
            if self.current_domain == None:
                self.current_domain = self.frontier.get_domain()
                if self.current_domain == None:
                    self.frontier.active_workers[self.id] = False
                    if self.frontier.not_running():
                        self.logger.info(f"Ending Thread")
                        return
                    time.sleep(6)
                    continue

            tbd_url = self.frontier.get_tbd_url(self.current_domain)
            if not tbd_url:
                self.logger.info("Domain is empty. Switching Domains.")
                del self.frontier.domain_list[domain]
                self.current_domain = None
                continue
            parsed_url = urlparse(tbd_url)
            domain = parsed_url.netloc
            """if domain in self.frontier.domain_list.keys():
                self.logger.info("Already visited")
            else:
                self.logger.info(f"Visited {domain} for the first time")
                self.frontier.domain_list[domain] = 0"""
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
                self.logger.info(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
