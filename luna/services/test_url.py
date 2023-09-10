from luna.services.url import UrlService


def test_root_domain():
    processor = UrlService("https://social.sda1.net")
    assert processor.domain() == "social.sda1.net"
    assert processor.root_domain() == "sda1.net"

    processor = UrlService("http://google.com")
    assert processor.domain() == "google.com"
    assert processor.root_domain() == "google.com"