from luna.services.search import SearchService


def test_blocklist():
    processor = SearchService()
    trash = [{"url": 'https://www.sejuku.net/blog',
                  "url": 'http://techacademy.jp/none'}]

    websites = [{"url": 'https://www.jp.square-enix.com/nierautomata/',
                  "url": 'https://github.com/nexryai/luna-search/actions'}]

    _trash = processor.optimize(trash)
    _websites = processor.optimize(websites)

    assert len(_trash) == 0
    assert len(_websites) == len(websites)