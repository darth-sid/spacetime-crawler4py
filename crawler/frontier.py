import os
import shelve

from threading import Thread, RLock
from queue import Queue, Empty

from utils import get_logger, get_urlhash, normalize
from scraper import is_valid

import time
from urllib.parse import urlparse

class Frontier(object):
    def __init__(self, config, restart):
        self.logger = get_logger("FRONTIER")
        self.config = config
        self.to_be_downloaded = list()
        self.active_domains = list()
        self.domain_list = {}
        self.active_workers = {}

        if not os.path.exists(self.config.save_file) and not restart:
            # Save file does not exist, but request to load save.
            self.logger.info(
                f"Did not find save file {self.config.save_file}, "
                f"starting from seed.")
        elif os.path.exists(self.config.save_file) and restart:
            # Save file does exists, but request to start from seed.
            self.logger.info(
                f"Found save file {self.config.save_file}, deleting it.")
            os.remove(self.config.save_file)

        if restart and os.path.exists('cache.shelve'):
            self.logger.info("Deleted cache file")
            os.remove('cache.shelve')
            shelve.open('cache.shelve')

        # Load existing save file, or create one if it does not exist.
        self.save = shelve.open(self.config.save_file)
        if restart:
            for url in self.config.seed_urls:
                assert(is_valid(url))
                self.add_url(url)
        else:
            # Set the frontier state with contents of save file.
            self._parse_save_file()
            if not self.save:
                for url in self.config.seed_urls:
                    self.add_url(url)

    def _parse_save_file(self):
        ''' This function can be overridden for alternate saving techniques. '''
        total_count = len(self.save)
        tbd_count = 0
        for url, completed in self.save.values():
            if not completed and is_valid(url):
                parsed_url = urlparse(url)
                domain = parsed_url.netloc
                if domain in self.domain_list.keys():
                    self.domain_list[domain].append(url)
                else:
                    self.domain_list[domain] = list()
                    self.domain_list[domain].append(url)
                    self.active_domains.append(domain)

                tbd_count += 1
        self.logger.info(
            f"Found {tbd_count} urls to be downloaded from {total_count} "
            f"total urls discovered.")

    def get_domain(self):
        try:
            return self.active_domains.pop()
        except IndexError:
            return None

    def not_running(self):
        for key in self.active_workers.keys():
            #self.logger.info(f"{key} {self.active_workers[key]}")
            if self.active_workers[key]:
                return False
        return True

    def get_tbd_url(self, domain):
        try:
            return self.domain_list[domain].pop()
        except IndexError:
            return None

    def add_url(self, url):
        url = normalize(url)
        urlhash = get_urlhash(url)
        if urlhash not in self.save:
            self.save[urlhash] = (url, False)
            self.save.sync()
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            if domain in self.domain_list.keys():
                self.domain_list[domain].append(url)
            else:
                self.domain_list[domain] = list()
                self.domain_list[domain].append(url)
                self.active_domains.append(domain)

    def mark_url_complete(self, url):
        urlhash = get_urlhash(url)
        if urlhash not in self.save:
            # This should not happen.
            self.logger.error(
                f"Completed url {url}, but have not seen it before.")

        self.save[urlhash] = (url, True)
        self.save.sync()
