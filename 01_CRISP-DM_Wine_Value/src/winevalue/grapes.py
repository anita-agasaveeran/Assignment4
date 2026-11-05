"""Grape-name synonyms and wine colour.

Frozen in Phase 2 revision 3; RE-FROZEN in Phase 3 (2026-11-04) and amended in Phase 3 revision 2 (same day), always
before any colour x value table or lockbox use: title override on the winery-stripped title with strict patterns
(+ US Port, still Blanc de Noir, Clairet; negative tests); amended again in revision 3
(Blanc de Noir yields to sparkling cues, critic round 2 N1); Muscat family merged; more grapes mapped. Wines whose
colour stays 'unmapped' are excluded from H5.

The raw ``variety`` label is kept unchanged for the frozen Phase 1 simple rules and the variety x
country baseline. ``grape_canonical`` merges labels that name the same grape in different languages or
markets, for DM4 (descriptor <-> grape rules), H5 (colour) and app navigation. The label itself still
carries style/market information and can stay a separate feature.

Muscat merges the white Muscat family (Canelli, Blanc à Petits Grains, Ottonel, Zibibbo, …; a documented
simplification); black/rosé Muscats map to 'Muscat (black)'.
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
    "Sylvaner": "Silvaner", "Prugnolo Gentile": "Sangiovese",
    "Muscat Canelli": "Muscat", "Gelber Muskateller": "Muscat", "Zibibbo": "Muscat", "Muskat Ottonel": "Muscat",
    "Orange Muscat": "Muscat", "Moscato Giallo": "Muscat", "Muscat Blanc": "Muscat", "Muscat Blanc à Petits Grains": "Muscat",
    "Moscatel de Alejandría": "Muscat", "Muskateller": "Muscat", "Black Muscat": "Muscat (black)", "Moscato Rosa": "Muscat (black)", "Tinta Fina": "Tempranillo", "Tinta del Pais": "Tempranillo",
    "Gamay Noir": "Gamay", "Carignano": "Carignan", "Assyrtico": "Assyrtiko",
    "Petite Verdot": "Petit Verdot", "Inzolia": "Insolia", "Meunier": "Pinot Meunier",
}

RED = {
    "Pinot Noir", "Cabernet Sauvignon", "Merlot", "Syrah", "Zinfandel", "Malbec", "Sangiovese", "Nebbiolo",
    "Tempranillo", "Cabernet Franc", "Grenache", "Gamay", "Petite Sirah", "Barbera", "Carmenère", "Aglianico",
    "Nero d'Avola", "Petit Verdot", "Blaufränkisch", "Mourvèdre", "Montepulciano", "Zweigelt", "Touriga Nacional",
    "Dolcetto", "Tannat", "Mencía", "Pinotage", "Nerello Mascalese", "Bonarda", "Sagrantino", "St. Laurent",
    "Negroamaro", "Lagrein", "Carignan", "Agiorgitiko", "Cinsault", "Baga", "Xinomavro", "Teroldego", "Graciano", "Frappato", "Muscat (black)", "Claret", "Saperavi", "Pinot Meunier", "Dornfelder",
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
    "Müller-Thurgau", "Traminer", "Fernão Pires", "Malvasia", "Gros and Petit Manseng", "Gros Manseng",
    "Aligoté", "Moschofilero", "Insolia", "Kerner",
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


# Style words in the TITLE override the grape colour (text only): a Pinot Noir rosé, a Chardonnay Brut, a tawny Port.
# Phase 3 re-freeze (2026-11-04, before H5 uses the map): matched on the title with the WINERY NAME REMOVED, with
# strict patterns, because winery and vineyard names ("Château du Port", "Cava d'Onice", "Coste di Rose",
# "Roger Rose Vineyard", "Porto Vecchio", "Tinto Fino") produced ~200 false positives in Phase 2.
_TITLE_STYLE = [
    (r"\bbrut\b|\bbruto\b|\bsparkling\b(?!\s+(?:hill|ridge|pointe?|vineyards?))|\bspumante\b|\bespumante\b|"
     r"\bchampagne\b(?!\s+(?:ridge|hill|vineyards?))|\(cava\)|\bcrémant\b|\bcremant\b|\bsekt\b|\(franciacorta\)|\bprosecco\b|pét-nat|\bpetillant\b|"
     r"\bbubbles\b|\bdosage zero\b|\bméthode (?:champenoise|traditionnelle)\b",
     "sparkling"),
    (r"\((?:port|porto|sherry|madeira|marsala|jerez|montilla-moriles)\)|\btawny\b(?!\s+(?:ridge|hill|vineyards?))|\boloroso\b|"
     r"\bamontillado\b|(?<!tinto )\bfino\b(?= .*\((?:jerez|sherry|montilla))|"
     r"\b(?:19|20)\d{2}\s+port\b(?!\s+(?:vineyards?|ranch|road|hill))|\bport\s+(?:zinfandel|syrah|petite sirah|cabernet|style)\b",
     "fortified"),
    (r"\brosé\b|\brose of\b|\brosé of\b|\brosé de\b|\bbrut rose\b|\brosado\b|\brosato\b|\bclairet\b", "rosé"),
]
# "Blanc de Noir(s)" (white wine from red grapes) is mostly a SPARKLING term. Phase 3 revision 3 (2026-11-04, critic round 2
# N1; text only, before any colour x value table): applied only AFTER the sparkling title cues and a sparkling variety label
# have failed; then sparkling if the note describes bubbles, else a still white (German/Austrian/US still Blanc de Noir).
_BLANC_DE_NOIR = r"\bblanc de noirs?\b"
_NOTE_BUBBLES = r"\bbubbl|\bmousse\b|\bfizz|\bbeads?\b|\bsparkl|\beffervesc|\bperlage\b|\bfrothy\b|\bspritz|\btirage\b|\bon the yeast\b|\bdisgorg"
def _grape_colour(v: str) -> str:
    g = SYNONYMS.get(v, v)
    if g in SPARKLING: return "sparkling"
    if g in FORTIFIED: return "fortified"
    if g == "Rosé": return "rosé"
    if g in RED: return "red"
    if g in WHITE: return "white"
    return "unmapped"


def wine_colour(variety: pd.Series, title: pd.Series | None = None, winery: pd.Series | None = None,
                note: pd.Series | None = None) -> pd.Series:
    """red / white / rosé / sparkling / fortified / unmapped, from grape knowledge and text only (never scores).

    Order: (1) a sparkling, fortified or rosé style word in the title (winery name removed) wins; (2) a sparkling
    variety label ("Sparkling Blend", "Champagne Blend", Glera); (3) "Blanc de Noir(s)": sparkling if the note describes
    bubbles, else white; (4) the grape's colour; (5) for blends ("Tempranillo Blend", "Grenache-Syrah"), the
    first-listed grape's colour; (6) keyword rules on the label ("Red Blend", ...); else unmapped.
    """
    blank = pd.Series([None] * len(variety), index=variety.index)
    titles = title if title is not None else blank
    notes = note if note is not None else blank
    if winery is not None:   # strip the winery name so its words can't trigger a style override
        titles = pd.Series([t[len(w):] if isinstance(t, str) and isinstance(w, str) and t.startswith(w) else t
                            for t, w in zip(titles, winery)], index=variety.index)

    def label_colour(v):
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

    def one(v, t, n):
        if isinstance(t, str):
            for pat, colour in _TITLE_STYLE:
                if re.search(pat, t, flags=re.IGNORECASE):
                    return colour
        c = label_colour(v) if isinstance(v, str) else "unmapped"
        if c == "sparkling":
            return c
        if isinstance(t, str) and re.search(_BLANC_DE_NOIR, t, flags=re.IGNORECASE):
            return "sparkling" if isinstance(n, str) and re.search(_NOTE_BUBBLES, n, flags=re.IGNORECASE) else "white"
        return c
    return pd.Series([one(v, t, n) for v, t, n in zip(variety, titles, notes)], index=variety.index)
