from luna.helpers import detect_lang


def test_detect_lang():
    assert detect_lang("nexryai is a cat") == "other"
    assert detect_lang("nexryaiは美少女です") == "ja"
    assert detect_lang("カタカナはカクカクしていますが、ひらがなはそうではありません。") == "ja"
    assert detect_lang("崩坏：星穹铁道") == "zh"