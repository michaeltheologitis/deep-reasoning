"""Design §7.3 through dr-acp's front: D3's falsifier, below the panel."""

import pytest

from deep_reasoning.acp.runlog import Home, SessionIndex
from deep_reasoning.acp.testing.fake_model import FakeOpenAI
from deep_reasoning.library import Library, library_path
from tests.acp.harness import dr_acp, run, run_ids
from tests.acp.scenarios import BASE_CONFIG, repl
from tests.library.conftest import ROUTER, example, text, user_texts, write_config

V1 = "Summarize each course, then rank them."
V2 = "Rank the courses by workload, then summarize."


@pytest.mark.parametrize("edit", [False, True], ids=["saved", "edited"])
def test_a_saved_decomposition_reaches_the_next_conversation_in_its_namespace(
    tmp_path, home, work, edit
):
    async def body():
        async with FakeOpenAI(lambda messages: repl("FinalAnswer('done')")) as model:
            config = {
                **ROUTER,
                "client": {**BASE_CONFIG["client"], "base_url": model.base_url},
            }
            lib = Library.open(library_path(home), starter=False)
            lib.import_config(write_config(tmp_path / "router", config))
            saved = lib.put_decomposition(
                text(example("summarize then rank", V1)),
                namespaces=["router"],
                use_when="comparing many courses",
            )
            if edit:
                saved = lib.put_decomposition(
                    text(example("summarize then rank", V2)),
                    use_when="comparing many courses",
                )
            async with dr_acp(None, home) as client:
                session = await client.open_session(work)
                menu = {c.name: c for c in client.printer.commands[session]}
                response = await client.ask(session, "Which course comes after CS101?")
                (run_id,) = run_ids(client.printer.updates)
                start = client.run_log(run_id)[0]
            index = SessionIndex.load(Home(home), session)
            return (
                saved,
                menu,
                response,
                start,
                index,
                user_texts(model.calls[0].messages),
            )

    saved, menu, response, start, index, asked = run(body())
    assert index.source == {"kind": "library", "library": str(library_path(home))}
    assert menu["summarize-then-rank"].description == "comparing many courses"
    assert response.field_meta["deep_reasoner"]["outcome"] == "answered"
    assert start.namespace == "router"
    assert (
        start.source["versions"]["decompositions"]["summarize then rank"]
        == saved.version
    )
    assert saved.version == (2 if edit else 1)
    assert (V2 if edit else V1) in asked
    assert (V1 if edit else V2) not in asked
