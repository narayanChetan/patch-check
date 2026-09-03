from app.services import ingredient_screener


def test_flags_banned_bakery_additive():
    text = "Ingredients: Wheat Flour, Sugar, Potassium Bromate, Salt"
    flags = ingredient_screener.screen_text(text)
    ids = [f.id for f in flags]
    assert "potassium_bromate" in ids


def test_high_severity_sorted_first():
    text = "Ingredients: Monosodium Glutamate, Potassium Bromate, Sugar"
    flags = ingredient_screener.screen_text(text)
    assert flags[0].id == "potassium_bromate"  # high severity before low (MSG)


def test_no_false_positive_on_clean_ingredients():
    text = "Ingredients: Wheat Flour, Water, Salt, Yeast, Sugar"
    flags = ingredient_screener.screen_text(text)
    assert flags == []


def test_quantity_hint_picked_up_when_present():
    text = "Contains Sodium Benzoate (0.05%) as a preservative"
    flags = ingredient_screener.screen_text(text)
    flag = next(f for f in flags if f.id == "sodium_benzoate")
    assert flag.quantity_hint is not None
    assert "0.05" in flag.quantity_hint


def test_no_duplicate_flags_for_same_ingredient_mentioned_twice():
    text = "Contains MSG. Also known as Monosodium Glutamate."
    flags = ingredient_screener.screen_text(text)
    ids = [f.id for f in flags]
    assert ids.count("msg") <= 1
