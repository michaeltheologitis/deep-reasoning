from deep_reasoning.tools import texts


def test_the_sentences_that_name_the_product_are_the_designs_verbatim():
    assert texts.reserved_name("task") == (
        "'task' is one of Deep Reasoning's own names in the REPL (subagent, run_all, "
        "FinalAnswer, Var, Func, task); a tool by that name would hide it. Choose another "
        "name."
    )
    assert texts.ready_timeout(30.0) == (
        "Check could not start Deep Reasoning within 30 s, so it did not build the tool. "
        "Try again."
    )
    assert texts.builtin("rag") == (
        "'rag' is one of Deep Reasoning's own factories. It is built when a conversation "
        "starts, with your model and files, so Check does not build it here."
    )
