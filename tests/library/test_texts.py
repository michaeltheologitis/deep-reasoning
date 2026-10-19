from deep_reasoning.library import texts


def test_the_sentences_that_name_the_product_are_the_designs_verbatim():
    assert texts.UI_NOT_BUILT == (
        "The panel's files are not in this installation: reinstall Deep Reasoning, or run "
        "npm run build in canvas-app/."
    )
