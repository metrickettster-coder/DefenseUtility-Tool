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


def test_search_standards():
    results = search("technical data package")
    assert any(r.id == "MIL-STD-31000B" and r.source == "mil_std" for r in results)


def test_search_standards_cited_document():
    results = search("dimensioning and tolerancing")
    assert any(r.id == "ASME Y14.5" for r in results)


def test_search_data_rights_clause():
    results = search("noncommercial computer software")
    assert any(r.id == "DFARS 252.227-7014" for r in results)


def test_search_clifs_criteria():
    results = search("CLIFS")
    assert any(r.id == "DOD-STD-2101 §3.1.6" for r in results)


def test_search_did_structure():
    results = search("abstract-reference")
    assert any(r.id == "MIL-STD-963 §4.2" for r in results)


def test_search_standards_no_duplicate_ids():
    from defenseutility.datastore import load_standards
    ids = [s["id"] for s in load_standards()]
    assert len(ids) == len(set(ids))
