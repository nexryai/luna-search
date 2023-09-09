from urllib.parse import urlparse


class UrlService:
    def __init__(self, url: str):
        self.url = url

    def domain(self) -> str:
        parsed_url = urlparse(self.url)
        domain = parsed_url.netloc
        return domain

    def root_domain(self) -> str:
        parsed_url = urlparse(self.url)
        domain_parts = parsed_url.netloc.split('.')

        if len(domain_parts) >= 2:  # At least a second-level domain and top-level domain are expected
            root_domain = '.'.join(domain_parts[-2:])
            return root_domain
        else:
            raise ValueError
