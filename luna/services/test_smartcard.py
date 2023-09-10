import time

from luna.services.smartcard import get_wikidata_id_from_query


def test_get_wikidata_id_from_query():
    assert get_wikidata_id_from_query("Mozilla Firefox") == "Q698"
    time.sleep(2)

    assert get_wikidata_id_from_query("systemd") == "Q286124"
    time.sleep(2)

    assert get_wikidata_id_from_query("Genshin Impact") == "Q65059474"
    time.sleep(2)

    assert get_wikidata_id_from_query("崩壊スターレイル") == "Q108896777"