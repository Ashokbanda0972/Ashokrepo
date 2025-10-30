def score_listing(listing: dict) -> float:
    """
    Simple heuristic scoring:
      - larger lot_size adds points
      - older year_built (pre-1950) adds points (potential teardown)
      - lower price/lot_sqft increases score
      - keywords in description add points
    """
    score = 0.0
    lot = listing.get("lot_size") or 0
    year = listing.get("year_built") or 9999
    price = listing.get("price") or 1

    # Lot size weight
    score += min(lot / 1000.0, 10.0)

    # Age weight: older house higher score
    if year and year < 1950:
        score += 5.0
    elif year and year < 1980:
        score += 2.0

    # Price per sqft (lower price per lot gives potential)
    pps = price / (lot+1)
    if pps < 50:
        score += 5.0
    elif pps < 200:
        score += 2.0

    # Keyword boost
    text = (listing.get("description") or "").lower()
    keywords = ["tear down", "tear-down", "builder", "contractor special", "development opportunity", "as is"]
    for k in keywords:
        if k in text:
            score += 3.0

    # classification override
    label = listing.get("classified_label")
    if label == "development":
        score *= 1.5
    elif label == "maybe":
        score *= 1.1

    return round(score, 3)
