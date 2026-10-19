from deep_reasoning.library import texts


def test_the_sentences_that_name_the_product_are_the_designs_verbatim():
    assert texts.UI_NOT_BUILT == (
        "The panel's files are not in this installation: reinstall Deep Reasoning, or run "
        "npm run build in canvas-app/."
    )
    assert texts.invalid("x", "Decomposition", [("name", "bad")]) == (
        "'x' is not a valid Deep Reasoning Decomposition:\n  name: bad"
    )
    assert texts.import_load("/c/main.yaml", "boom") == (
        "/c/main.yaml is not a dr config Deep Reasoning can load: boom"
    )
