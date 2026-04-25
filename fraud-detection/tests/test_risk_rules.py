from risk_rules import label_risk, score_transaction


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_tx(**overrides):
    """Minimal clean transaction — all signals at their zero-risk values."""
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


# ---------------------------------------------------------------------------
# label_risk — boundary conditions
# ---------------------------------------------------------------------------

def test_label_risk_low_boundary():
    assert label_risk(0) == "low"
    assert label_risk(29) == "low"


def test_label_risk_medium_boundary():
    assert label_risk(30) == "medium"
    assert label_risk(59) == "medium"


def test_label_risk_high_boundary():
    assert label_risk(60) == "high"
    assert label_risk(100) == "high"


# ---------------------------------------------------------------------------
# Clean transaction baseline
# ---------------------------------------------------------------------------

def test_clean_transaction_scores_zero():
    assert score_transaction(_base_tx()) == 0


# ---------------------------------------------------------------------------
# Device risk score — exact point values for each tier
# ---------------------------------------------------------------------------

def test_device_risk_low_tier_no_points():
    assert score_transaction(_base_tx(device_risk_score=39)) == 0


def test_device_risk_medium_tier_adds_10():
    assert score_transaction(_base_tx(device_risk_score=40)) == 10
    assert score_transaction(_base_tx(device_risk_score=69)) == 10


def test_device_risk_high_tier_adds_25():
    assert score_transaction(_base_tx(device_risk_score=70)) == 25
    assert score_transaction(_base_tx(device_risk_score=100)) == 25


def test_high_device_risk_increases_score():
    assert score_transaction(_base_tx(device_risk_score=75)) > score_transaction(_base_tx(device_risk_score=10))


# ---------------------------------------------------------------------------
# International flag — exact point value
# ---------------------------------------------------------------------------

def test_international_adds_15():
    assert score_transaction(_base_tx(is_international=1)) == 15


def test_domestic_adds_nothing():
    assert score_transaction(_base_tx(is_international=0)) == 0


def test_international_increases_score():
    assert score_transaction(_base_tx(is_international=1)) > score_transaction(_base_tx(is_international=0))


# ---------------------------------------------------------------------------
# Transaction amount — exact point values for each tier
# ---------------------------------------------------------------------------

def test_small_amount_adds_nothing():
    assert score_transaction(_base_tx(amount_usd=499)) == 0


def test_medium_amount_adds_10():
    assert score_transaction(_base_tx(amount_usd=500)) == 10
    assert score_transaction(_base_tx(amount_usd=999)) == 10


def test_large_amount_adds_25():
    assert score_transaction(_base_tx(amount_usd=1000)) == 25
    assert score_transaction(_base_tx(amount_usd=1200)) == 25


# ---------------------------------------------------------------------------
# Velocity — exact point values for each tier
# ---------------------------------------------------------------------------

def test_low_velocity_adds_nothing():
    assert score_transaction(_base_tx(velocity_24h=2)) == 0


def test_medium_velocity_adds_5():
    assert score_transaction(_base_tx(velocity_24h=3)) == 5
    assert score_transaction(_base_tx(velocity_24h=5)) == 5


def test_high_velocity_adds_20():
    assert score_transaction(_base_tx(velocity_24h=6)) == 20
    assert score_transaction(_base_tx(velocity_24h=10)) == 20


def test_high_velocity_increases_score():
    assert score_transaction(_base_tx(velocity_24h=8)) > score_transaction(_base_tx(velocity_24h=1))


# ---------------------------------------------------------------------------
# Failed logins — exact point values for each tier
# ---------------------------------------------------------------------------

def test_no_failed_logins_adds_nothing():
    assert score_transaction(_base_tx(failed_logins_24h=0)) == 0
    assert score_transaction(_base_tx(failed_logins_24h=1)) == 0


def test_moderate_failed_logins_adds_10():
    assert score_transaction(_base_tx(failed_logins_24h=2)) == 10
    assert score_transaction(_base_tx(failed_logins_24h=4)) == 10


def test_high_failed_logins_adds_20():
    assert score_transaction(_base_tx(failed_logins_24h=5)) == 20
    assert score_transaction(_base_tx(failed_logins_24h=9)) == 20


def test_failed_logins_increases_score():
    assert score_transaction(_base_tx(failed_logins_24h=5)) > score_transaction(_base_tx(failed_logins_24h=0))


# ---------------------------------------------------------------------------
# Prior chargebacks — exact point values for each tier
# ---------------------------------------------------------------------------

def test_no_prior_chargebacks_adds_nothing():
    assert score_transaction(_base_tx(prior_chargebacks=0)) == 0


def test_one_prior_chargeback_adds_5():
    assert score_transaction(_base_tx(prior_chargebacks=1)) == 5


def test_two_plus_prior_chargebacks_adds_20():
    assert score_transaction(_base_tx(prior_chargebacks=2)) == 20
    assert score_transaction(_base_tx(prior_chargebacks=5)) == 20


def test_prior_chargebacks_increase_score():
    clean = score_transaction(_base_tx(prior_chargebacks=0))
    one_cb = score_transaction(_base_tx(prior_chargebacks=1))
    two_cb = score_transaction(_base_tx(prior_chargebacks=2))
    assert one_cb > clean
    assert two_cb > one_cb


# ---------------------------------------------------------------------------
# Multi-signal accumulation
# ---------------------------------------------------------------------------

def test_independent_signals_accumulate():
    # international (15) + high velocity (20) = 35
    score = score_transaction(_base_tx(is_international=1, velocity_24h=8))
    assert score == 35


def test_all_high_risk_signals_accumulate():
    # device 75 (25) + international (15) + amount 1200 (25) +
    # velocity 8 (20) + logins 6 (20) + chargebacks 3 (20) = 125 → clamped to 100
    tx = _base_tx(
        device_risk_score=75,
        is_international=1,
        amount_usd=1200,
        velocity_24h=8,
        failed_logins_24h=6,
        prior_chargebacks=3,
    )
    assert score_transaction(tx) == 100


# ---------------------------------------------------------------------------
# Score clamping
# ---------------------------------------------------------------------------

def test_score_never_exceeds_100():
    tx = _base_tx(
        device_risk_score=100,
        is_international=1,
        amount_usd=9999,
        velocity_24h=99,
        failed_logins_24h=99,
        prior_chargebacks=99,
    )
    assert score_transaction(tx) == 100


def test_score_never_goes_below_zero():
    assert score_transaction(_base_tx()) == 0
