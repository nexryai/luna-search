import time

from luna.services.smartcard import get_wikidata_id_from_query, SmartcardService


def test_smartcard():
    processor = SmartcardService("Q108896777")
    result = processor.get_info("ja")
    assert type(result["label"]) == str
    assert type(result["description"]) == str
    assert type(result["official_website"]) == str


def test_get_wikidata_id_from_query():
    assert get_wikidata_id_from_query("Mozilla Firefox") == "Q698"
    time.sleep(2)

    assert get_wikidata_id_from_query("systemd") == "Q286124"
    time.sleep(2)

    assert get_wikidata_id_from_query("Genshin Impact") == "Q65059474"
    time.sleep(2)

    assert get_wikidata_id_from_query("崩壊スターレイル") == "Q108896777"