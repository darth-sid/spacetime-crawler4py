import re, os
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from bs4 import BeautifulSoup
import shelve
import analyze_links as al
from utils import get_logger, get_urlhash

save = shelve.open("unique_links.shelve")
logger = get_logger("Crawler", "CRAWLER")

def normalized_hash(parsed_url):
    # queries to ignore
    ignore = {'utm_source','utm_medium','utm_campaign','utm_term','utm_content',
              'sessionid','sessid','sid','phpsessid','aspsessionid','jsessionid',
              'date','time','calendar','schedule',
              'ref','referrer','src','sort','order','orderby','direction','view','display',
              'clid','click_id','aff_id','aid','affilliate_id','aff_sub', 'banner_id', 'campaign_id',
              }
    netloc = parsed_url.netloc
    if netloc.startswith("www."):
        netloc = netloc[4:]

    path = parsed_url.path
    if path.endswith("index.html"):
        path = path[:-10]
    elif path.endswith("index.htm"):
        path = path[:-9]

    query = parse_qs(parsed_url.query)
    filtered_query = dict(query)
    for param in query:
        if param in ignore:
            filtered_query.pop(param, None)
    query = urlencode(filtered_query, doseq=True)

    url = urlunparse(('',netloc,path,'',query,''))
    return get_urlhash(url)

def scraper(url, resp):
    if not is_valid(url):
        return []
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    links = []
    if resp.status == 200:
        soup = BeautifulSoup(resp.raw_response.content,'html.parser')
        robot_tag = soup.find("meta", attrs={"name": "robots"})
        if robot_tag:
            content = robot_tag.get('content')
            if 'nofollow' in content or 'noindex' in content:
                return []
        if al.getWords(soup) > 0:
            logger.info(url) # log urls that arent low information
        links = [link['href'] for link in soup.find_all('a',href=True) if link['rel'] == "nofollow"]
    return links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    
    #ignore calendars traps, login pages, 
    banned_paths = ['calendar'] # TODO

    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        valid = not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|ttf|otf|woff|woff2|eot|fon"
            + r"|img|pkg|exe|msi|sql|db|mdb|log|sqlite"
            + r"|cpp|py|pix|bib|war|ini|o|a|lib|obj|ini|config"
            + r"|raw|ods|key|odp|ods|numbers|bat|sh|bak|swp"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|z|xz|lz|tgz|tbz|apk|ipa)$", parsed.path.lower())
        if not valid:
            return False

        valid_domain = bool(re.match(r"^(.*\.)?ics\.uci\.edu$"
                + r"|^(.*\.)?cs\.uci\.edu$"
                + r"|^(.*\.)?informatics\.uci\.edu$"
                + r"|^(.*\.)?stat\.uci\.edu$", parsed.netloc) or
                (re.match(r"^today\.uci\.edu/$", parsed.netloc) and 
                        re.match(r"^department/information_computer_sciences/.*$", parsed.path)))
        if not valid_domain:
            return False

        for path in banned_paths:
            if re.search(path, parsed.path, re.IGNORECASE) is not None:
                return False
        
        paths = path.split('/')
        counts = {}
        for p in paths:
            if p not in counts:
                counts[p] = 0
            counts[p] += 1
            if counts[p] > 2:
                return False # invalid if any path is repeated more than twice to avoid repetitive path traps


        # check for xxxx-xx-xx in queries to avoid calendar traps
        if re.search(r"\b\d{4}-\d{2}-\d{2}\b", parsed.query) is not None:
            return False
        if re.search(r"\b\d{4}-\d{2}\b", parsed.query) is not None:
            return False
        # check for xxxx-xx-xx in queries to avoid calendar traps
        if re.search(r"\b\d{4}-\d{2}-\d{2}\b", parsed.path) is not None:
            return False
        if re.search(r"\b\d{4}-\d{2}\b", parsed.path) is not None:
            return False

        # cache unique urls visited
        url = f"{parsed.netloc}{parsed.path}?{parsed.query}"
        urlhash = normalized_hash(parsed)
        if urlhash in save:
            return False
        save[urlhash] = url

        
        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise
