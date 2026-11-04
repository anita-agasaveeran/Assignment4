import pytest

from bakery.metrics import fill_rate, mae, waste_rate, waste_units, wape


def test_forecast_metrics():
    assert mae([10, 20], [12, 17]) == 2.5
    assert wape([10, 30], [12, 27]) == pytest.approx(100 * 5 / 40)


def test_business_metrics():
    demand, baked = [10, 20, 5], [12, 15, 5]
    assert waste_units(demand, baked) == 2
    assert fill_rate(demand, baked) == pytest.approx(30 / 35)
    assert waste_rate(demand, baked) == pytest.approx(2 / 32)


def test_metric_guards():
    with pytest.raises(ValueError):
        wape([0, 0], [1, 1])
    with pytest.raises(ValueError):
        mae([1, 2], [1])


