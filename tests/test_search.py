from defenseutility.search import search


def test_search_by_id():
    results = search("252.204-7012")
    assert any(r.id == "DFARS 252.204-7012" for r in results)


def test_search_by_keyword():
    results = search("multifactor")
    assert any(r.id == "3.5.3" for r in results)


def test_search_no_match():
    assert search("zzz_not_a_real_term_zzz") == []


def test_search_source_filter():
    results = search("incident", sources=("clauses",))
    assert all(r.source == "clause" for r in results)
