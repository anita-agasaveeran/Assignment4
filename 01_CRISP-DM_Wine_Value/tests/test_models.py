import numpy as np
import pandas as pd

from winevalue.models import GroupMeanBaseline, quick_text_model


def test_group_mean_baseline_shrinks_and_falls_back():
    X = pd.DataFrame({"variety": ["A", "A", "B"], "country": ["X", "X", "Y"]})
    y = [90, 92, 84]
    m = GroupMeanBaseline(shrink=1).fit(X, y)          # global mean = 88.667
    pred = m.predict(pd.DataFrame({"variety": ["A", "Z"], "country": ["X", "X"]}))
    global_mean = (90 + 92 + 84) / 3
    assert np.isclose(pred[0], (2 * 91 + 1 * global_mean) / (2 + 1))   # n=2, mean 91, shrink=1
    assert np.isclose(pred[1], global_mean)                          # unseen group -> global mean


def test_quick_text_model_fits():
    X = pd.DataFrame({"description": ["crisp lemon acidity"] * 10 + ["rich ripe plum oak"] * 10,
                      "country": ["X"] * 20, "province": ["P"] * 20, "variety": ["A"] * 20,
                      "vintage": [2010.0] * 19 + [np.nan]})
    y = [86] * 10 + [92] * 10
    m = quick_text_model(alpha=0.1)
    m.named_steps["columntransformer"].set_params(text__min_df=1)
    pred = m.fit(X, y).predict(X)
    assert pred[:10].mean() < pred[10:].mean()
