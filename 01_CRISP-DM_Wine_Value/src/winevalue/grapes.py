"""Grape-name synonyms and wine colour (frozen in Phase 2 revision 3, before any colour x value table;
known title-override false positives and Muscat-family gaps are fixed in Phase 3, before H5 uses the map).

The raw ``variety`` label is kept unchanged for the frozen Phase 1 simple rules and the variety x
country baseline. ``grape_canonical`` merges labels that name the same grape in different languages or
markets, for DM4 (descriptor <-> grape rules), H5 (colour) and app navigation. The label itself still
carries style/market information and can stay a separate feature.

Muscat merges a family of distinct Muscat varieties (documented simplification).
Sources: standard ampelographic synonyms (e.g. the Vitis International Variety Catalogue, VIVC) and
general wine references. Assignments use grape knowledge only, never this dataset's scores.
"""

from __future__ import annotations

import re

import pandas as pd

SYNONYMS = {
    "Shiraz": "Syrah", "Pinot Grigio": "Pinot Gris", "Grauburgunder": "Pinot Gris",
    "Garnacha": "Grenache", "Cannonau": "Grenache", "Garnacha Tinta": "Grenache",
    "Primitivo": "Zinfandel", "Alvarinho": "Albariño", "Monastrell": "Mourvèdre", "Mataro": "Mourvèdre",
    "Pinot Bianco": "Pinot Blanc", "Weissburgunder": "Pinot Blanc", "Pinot Nero": "Pinot Noir",
    "Spätburgunder": "Pinot Noir", "Tinta de Toro": "Tempranillo", "Tinto Fino": "Tempranillo",
    "Tinta Roriz": "Tempranillo", "Tinto del Pais": "Tempranillo", "Aragonês": "Tempranillo",
    "Garnacha Blanca": "Grenache Blanc", "Moscato": "Muscat", "Moscatel": "Muscat", "Muskat": "Muscat",
    "Sangiovese Grosso": "Sangiovese", "Fumé Blanc": "Sauvignon Blanc", "Sauvignon": "Sauvignon Blanc",
    "Semillon": "Sémillon", "Carignane": "Carignan", "Cariñena": "Carignan", "Mazuelo": "Carignan",
    "Melon": "Melon de Bourgogne", "Turbiana": "Verdicchio", "Viura": "Macabeo",
    "Rosado": "Rosé", "Rosato": "Rosé", "Blaufränkisch": "Blaufränkisch", "Lemberger": "Blaufränkisch",
    "Kékfrankos": "Blaufränkisch", "Côt": "Malbec", "Auxerrois": "Auxerrois", "Glera": "Glera",
    "Prosecco": "Glera", "Ugni Blanc": "Trebbiano", "Petite Syrah": "Petite Sirah", "Durif": "Petite Sirah",
    "Sylvaner": "Silvaner", "Prugnolo Gentile": "Sangiovese", "Tinta Fina": "Tempranillo", "Tinta del Pais": "Tempranillo",
    "Gamay Noir": "Gamay", "Carignano": "Carignan", "Assyrtico": "Assyrtiko",
}

RED = {
    "Pinot Noir", "Cabernet Sauvignon", "Merlot", "Syrah", "Zinfandel", "Malbec", "Sangiovese", "Nebbiolo",
    "Tempranillo", "Cabernet Franc", "Grenache", "Gamay", "Petite Sirah", "Barbera", "Carmenère", "Aglianico",
    "Nero d'Avola", "Petit Verdot", "Blaufränkisch", "Mourvèdre", "Montepulciano", "Zweigelt", "Touriga Nacional",
    "Dolcetto", "Tannat", "Mencía", "Pinotage", "Nerello Mascalese", "Bonarda", "Sagrantino", "St. Laurent",
    "Negroamaro", "Lagrein", "Carignan", "Agiorgitiko", "Cinsault", "Baga", "Xinomavro", "Teroldego",
    "Alicante Bouschet", "Lambrusco", "Cabernet", "Corvina, Rondinella, Molinara", "Merlot-Cabernet Sauvignon", "Cabernet Sauvignon-Merlot",
    "Cabernet Sauvignon-Syrah", "Malbec-Merlot", "Malbec-Cabernet Sauvignon", "Syrah-Grenache", "G-S-M", "Meritage",
}
WHITE = {
    "Chardonnay", "Riesling", "Sauvignon Blanc", "Pinot Gris", "Grüner Veltliner", "Gewürztraminer", "Viognier",
    "Chenin Blanc", "Albariño", "Pinot Blanc", "Muscat", "Verdejo", "Melon de Bourgogne", "Garganega", "Torrontés",
    "Vermentino", "Roussanne", "Verdicchio", "Fiano", "Sémillon", "Vernaccia", "Silvaner",
    "Grenache Blanc", "Grillo", "Friulano", "Greco", "Macabeo", "Falanghina", "Arneis", "Godello",
    "Ribolla Gialla", "Arinto", "Cortese", "Marsanne", "Verdelho", "Petit Manseng", "Assyrtiko", "Furmint",
    "Trebbiano", "Pecorino", "Encruzado", "Loureiro", "Sauvignon Blanc-Semillon", "Semillon-Sauvignon Blanc",
}
SPARKLING = {"Glera"}
FORTIFIED = {"Port", "Sherry", "Madeira"}

_KEYWORDS = [  # applied to the raw label, in order, when the grape isn't in the explicit lists
    (r"spark|champagne|cava|crémant|cremant|espumante|sekt|franciacorta", "sparkling"),
    (r"\bport\b|sherry|madeira|marsala", "fortified"),
    (r"rosé|rosado|rosato|\brose\b", "rosé"),
    (r"\bred\b|tinto|rosso|\brouge\b", "red"),
    (r"\bwhite\b|blanco|bianco|\bblanc\b|branco", "white"),
]


def grape_canonical(variety: pd.Series) -> pd.Series:
    """Merge synonym labels into one grape name (labels not in SYNONYMS are kept as-is)."""
    return variety.map(lambda v: SYNONYMS.get(v, v) if isinstance(v, str) else v)


# Style words in the TITLE override the grape colour (text only): a Pinot Noir rosé, a Chardonnay Brut, a tawny Port
_TITLE_STYLE = [
    (r"\bbrut\b|sparkling|spumante|espumante|champagne|\bcava\b|crémant|cremant|\bsekt\b|franciacorta|prosecco|pét-nat|petillant", "sparkling"),
    (r"\bporto?\b|\btawny\b|sherry|madeira|marsala|\bfino\b|oloroso|amontillado", "fortified"),
    (r"rosé|rosado|rosato|\brose\b", "rosé"),
]


def _grape_colour(v: str) -> str:
    g = SYNONYMS.get(v, v)
    if g in SPARKLING: return "sparkling"
    if g in FORTIFIED: return "fortified"
    if g == "Rosé": return "rosé"
    if g in RED: return "red"
    if g in WHITE: return "white"
    return "unmapped"


def wine_colour(variety: pd.Series, title: pd.Series | None = None) -> pd.Series:
    """red / white / rosé / sparkling / fortified / unmapped, from grape knowledge and title style words only.

    Order: (1) a style word in the title (sparkling, fortified, rosé) wins; (2) the grape's colour;
    (3) for blends ("Tempranillo Blend", "Grenache-Syrah", "Shiraz-Viognier"), the first-listed grape's
    colour; (4) keyword rules on the label ("Red Blend", "Champagne Blend", ...); else unmapped.
    """
    titles = title if title is not None else pd.Series([None] * len(variety), index=variety.index)

    def one(v, t):
        if isinstance(t, str):
            for pat, colour in _TITLE_STYLE:
                if re.search(pat, t, flags=re.IGNORECASE):
                    return colour
        if not isinstance(v, str):
            return "unmapped"
        c = _grape_colour(v)
        if c != "unmapped":
            return c
        first = re.split(r"\s*[-,/]\s*|\s+Blend$", v)[0].strip()
        c = _grape_colour(first)
        if c != "unmapped":
            return c
        for pat, colour in _KEYWORDS:
            if re.search(pat, v, flags=re.IGNORECASE):
                return colour
        return "unmapped"
    return pd.Series([one(v, t) for v, t in zip(variety, titles)], index=variety.index)
