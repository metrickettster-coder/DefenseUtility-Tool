from defenseutility.compliance import check_document


def test_referenced_by_id():
    text = "This SOW incorporates DFARS 252.204-7012 and FAR 52.204-21."
    report = check_document(text, baseline_ids=["DFARS 252.204-7012", "FAR 52.204-21"])
    assert len(report.referenced) == 2
    assert len(report.missing) == 0
    assert report.coverage_ratio == 1.0


def test_referenced_by_keyword():
    text = "The contractor shall employ multifactor authentication for all privileged accounts."
    report = check_document(text, baseline_ids=["3.5.3"])
    assert len(report.referenced) == 1


def test_missing_item():
    text = "This document mentions nothing relevant."
    report = check_document(text, baseline_ids=["DFARS 252.204-7012"])
    assert len(report.missing) == 1
    assert report.coverage_ratio == 0.0


def test_unknown_baseline_id_is_skipped():
    report = check_document("some text", baseline_ids=["NOT-A-REAL-ID"])
    assert report.referenced == []
    assert report.missing == []
