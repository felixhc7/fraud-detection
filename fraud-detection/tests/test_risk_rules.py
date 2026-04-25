from risk_rules import label_risk, score_transaction


def _base_tx(**overrides):
    tx = {
        "device_risk_score": 10,
        "is_international": 0,
        "amount_usd": 100,
        "velocity_24h": 1,
        "failed_logins_24h": 0,
        "prior_chargebacks": 0,
    }
    tx.update(overrides)
    return tx


def test_label_risk_thresholds():
    assert label_risk(10) == "low"
    assert label_risk(35) == "medium"
    assert label_risk(75) == "high"


def test_large_amount_adds_risk():
    assert score_transaction(_base_tx(amount_usd=1200)) >= 25


def test_high_device_risk_increases_score():
    low = score_transaction(_base_tx(device_risk_score=10))
    high = score_transaction(_base_tx(device_risk_score=75))
    assert high > low


def test_international_increases_score():
    domestic = score_transaction(_base_tx(is_international=0))
    international = score_transaction(_base_tx(is_international=1))
    assert international > domestic


def test_high_velocity_increases_score():
    low_v = score_transaction(_base_tx(velocity_24h=1))
    high_v = score_transaction(_base_tx(velocity_24h=8))
    assert high_v > low_v


def test_prior_chargebacks_increase_score():
    clean = score_transaction(_base_tx(prior_chargebacks=0))
    one_cb = score_transaction(_base_tx(prior_chargebacks=1))
    two_cb = score_transaction(_base_tx(prior_chargebacks=2))
    assert one_cb > clean
    assert two_cb > one_cb
