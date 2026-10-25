"""Build the UI's showcase chats: made-up runs that show off the tree.

The sky chat is the brief's example. The degree chat delegates six levels deep, has a
failure that its parent recovers from, and has a course lookup at the bottom that
delegates again. The essays chat fans out to 3,000 sub-agents. Every cell's output comes
from running its code against stand-ins for the REPL's subagent(), run_all() and a
course catalog; the texts, costs and seconds are made up.

Run from the repo root: python3 scripts/mock_showcase.py
"""

import ast
import asyncio
import contextlib
import io
import json
import random
import traceback
from pathlib import Path
from types import SimpleNamespace

OUT = Path(__file__).resolve().parents[1] / "src/deep_reasoning/web/data/showcase.json"
CELL_FILE = "<cell>"
TIMEOUT = "the model did not answer within 120 s"
THINK_SECONDS = 1.4
CELL_SECONDS = 0.9
CODE_CHARS_PER_SECOND = 150
STEP_COST = 0.0006
COST_PER_CHAR = 0.000004
SEED = 2026
ESSAY_COUNT = 3000
FAILED_ESSAYS = 33
EXHAUSTED_ESSAYS = 8
BORDERLINE_ESSAYS = 9
COUNTED_SHARE = 0.3
MIN_WORDS = 500
ESSAY_LENGTH = (460, 1200)
GRADER_COST = (0.0008, 0.0016)
GRADER_SECONDS = (1.2, 4.0)
GRADE_WEIGHTS = {"A": 14, "B": 40, "C": 30, "D": 10, "F": 6}
COMMENTS = {
    "A": ["sharp thesis, well-chosen evidence.", "original argument, tight structure."],
    "B": ["clear thesis, thin evidence.", "solid argument, uneven paragraphs."],
    "C": ["the thesis drifts; mostly summary.", "readable but loosely argued."],
    "D": ["no clear thesis.", "claims without evidence."],
    "F": ["off topic.", "mostly restates the prompt."],
}
ESSAY_WORDS = [
    "the",
    "argument",
    "evidence",
    "shows",
    "that",
    "because",
    "thesis",
    "we",
]

BOTH = ["autumn", "spring"]
CATALOG = {
    "CS 161": ("Intro to Programming", 4, [], BOTH),
    "CS 162": ("Data Abstraction", 4, ["CS 161"], BOTH),
    "CS 201": ("Discrete Mathematics", 4, ["CS 161"], BOTH),
    "CS 221": ("Data Structures", 4, ["CS 162", "CS 201"], BOTH),
    "CS 311": ("Algorithms", 4, ["CS 221"], BOTH),
    "CS 341": ("Theory of Computation", 4, ["CS 201", "CS 221"], BOTH),
    "CS 351": ("Computer Systems", 4, ["CS 221"], BOTH),
    "CS 421": ("Advanced Algorithms", 4, ["CS 311"], ["autumn"]),
    "CS 431": ("Computational Complexity", 4, ["CS 311", "CS 341"], ["spring"]),
    "CS 451": ("Cryptography", 4, ["CS 311", "STAT 311"], ["autumn"]),
    "CS 461": ("Logic in Computer Science", 4, ["CS 341"], BOTH),
    "CS 499": ("Senior Thesis in Theory", 4, ["CS 431"], ["spring"]),
    "MATH 151": ("Calculus I", 5, [], BOTH),
    "MATH 152": ("Calculus II", 5, ["MATH 151"], BOTH),
    "MATH 241": ("Linear Algebra", 5, ["MATH 152"], BOTH),
    "MATH 301": ("Introduction to Proofs", 5, ["MATH 152"], BOTH),
    "MATH 340": ("Abstract Algebra", 5, ["MATH 301"], BOTH),
    "MATH 381": ("Combinatorics", 5, ["MATH 301"], ["spring"]),
    "STAT 311": ("Probability", 5, ["MATH 152"], BOTH),
    "STAT 421": ("Information Theory", 5, ["STAT 311"], ["spring"]),
    "PHIL 270": ("Symbolic Logic", 5, [], BOTH),
    "PHIL 345": ("Philosophy of Mathematics", 5, ["PHIL 270"], ["spring"]),
    "ECON 351": ("Game Theory", 5, ["MATH 152"], ["autumn"]),
    "LING 200": ("Introduction to Linguistics", 5, [], BOTH),
    "LING 340": ("Formal Languages", 5, ["LING 200"], ["spring"]),
    "PHYS 121": ("Mechanics", 5, ["MATH 151"], BOTH),
    "PHYS 225": ("Quantum Mechanics I", 5, ["PHYS 121", "MATH 241"], ["autumn"]),
    "PHYS 324": ("Quantum Computing", 5, ["PHYS 225", "CS 221"], ["spring"]),
}
NOTES = {"CS 341": "MATH 301 recommended"}

SKY_SPAWN = """\
parts = run_all({
    "scattering": anext(subagent().send("How does Rayleigh scattering depend on wavelength?")),
    "violet": anext(subagent().send("Violet scatters more than blue. Why isn't the sky violet?")),
    "sunset": anext(subagent().send("Why are sunsets red?")),
})
print(parts)"""

SKY_ANSWER = """\
The sky is blue because air scatters the short wavelengths of sunlight far more than the long ones.

- **Scattering.** Nitrogen and oxygen molecules are much smaller than the wavelength of light, so they scatter it with an intensity that goes as 1/λ⁴ (Rayleigh scattering). Light at 400 nm scatters about **9.4×** more than light at 700 nm.
- **Why not violet.** Sunlight carries less violet than blue, ozone absorbs some of it, and the eye is about **75×** less sensitive at 410 nm than at 470 nm. The scattered mix looks blue.
- **Sunsets.** Near the horizon sunlight crosses about **38×** more air than at noon, so most of the blue is scattered out of the beam before it reaches you, leaving red and orange."""

DEGREE_SPAWN = """\
parts = run_all({
    "core": anext(subagent().send("List the core courses every CS major must take.")),
    "theory": anext(subagent().send("Map the theory track: which courses, and what each needs first?")),
    "electives": anext(subagent().send("Which courses outside CS suit a student who loves theory?")),
})
for name, part in parts.items():
    print(f"{name}: {part}")"""

SCHEDULE = """\
from graphlib import TopologicalSorter

core = ["CS 161", "CS 162", "CS 201", "CS 221", "CS 311", "CS 351", "MATH 151", "MATH 152", "MATH 241", "STAT 311"]
theory = ["CS 341", "CS 421", "CS 431", "CS 451", "CS 461", "CS 499"]
electives = ["MATH 301", "MATH 340", "MATH 381", "PHIL 270", "ECON 351"]
needs = {c: course(c)["prereqs"] for c in core + theory + electives}
terms = ["autumn", "spring"]
semesters = [[] for _ in range(8)]
term_of = {}
for c in TopologicalSorter(needs).static_order():
    n = max((term_of[p] + 1 for p in needs[c]), default=0)
    while len(semesters[n]) == 3 or terms[n % 2] not in course(c)["terms"]:
        n += 1
    semesters[n].append(c)
    term_of[c] = n
plan = "\\n".join(f"Year {n // 2 + 1} {terms[n % 2]}: {', '.join(s)}" for n, s in enumerate(semesters))
print(plan)"""

CHECK_YEARS = """\
years = [semesters[n : n + 2] for n in range(0, 8, 2)]
checks = run_all([
    anext(subagent().send(f"Check year {y + 1}: autumn {', '.join(a)}; spring {', '.join(s)}."))
    for y, (a, s) in enumerate(years)
])
print("\\n".join(checks))"""

CHECK_PREREQS = """\
term_of = {c: n for n, chosen in enumerate(semesters) for c in chosen}
late = [(c, p) for c, n in term_of.items() for p in course(c)["prereqs"] if term_of[p] >= n]
print(late or "every prerequisite comes at least a term earlier")"""

ESSAYS_SPAWN = """\
from collections import Counter


async def grade(essay_id):
    try:
        return await anext(subagent().send(f"Grade essay {essay_id}."))
    except TimeoutError as error:
        return f"failed: {error}"


grades = run_all({essay_id: grade(essay_id) for essay_id in essays})
letters = Counter(g.split(":")[0] if ":" in g else "out of turns" for g in grades.values())
print(dict(sorted(letters.items())))"""

ESSAYS_UNGRADED = """\
ungraded = [e for e, g in grades.items() if g.split(":")[0] not in ("A", "B", "C", "D", "F")]
print(len(ungraded), "need a person:", ", ".join(ungraded))"""


def course(code):
    title, credits, prereqs, terms = CATALOG[code]
    entry = {"title": title, "credits": credits, "prereqs": prereqs, "terms": terms}
    return entry | ({"notes": NOTES[code]} if code in NOTES else {})


def courses(department):
    return [code for code in CATALOG if code.startswith(f"{department} ")]


def final_answer(value):
    print(f"FinalAnswer: {value!r}")


async def gather(calls):
    if isinstance(calls, dict):
        return dict(zip(calls, await asyncio.gather(*calls.values())))
    return await asyncio.gather(*calls)


def repl_tools(agents):
    """subagent() and run_all() as a cell sees them, answering from these mock sub-agents."""
    by_task = {agent["task"]: agent for agent in agents}

    def answer(task):
        if by_task[task]["status"] == "failed":
            raise TimeoutError(TIMEOUT)
        return by_task[task]["result"]

    async def send(task):
        yield answer(task)

    def subagent(task=None):
        return SimpleNamespace(send=send) if task is None else answer(task)

    return {"subagent": subagent, "run_all": lambda calls: asyncio.run(gather(calls))}


def traceback_text(error):
    frames = traceback.extract_tb(error.__traceback__)
    in_cell = [frame for frame in frames if frame.filename == CELL_FILE]
    lines = traceback.format_list(in_cell) + traceback.format_exception_only(error)
    return "Traceback (most recent call last):\n" + "".join(lines).rstrip("\n")


def run(code, env):
    """What a cell prints, and whether it raised, the way the REPL reports it."""
    printed = io.StringIO()
    try:
        with contextlib.redirect_stdout(printed):
            exec(compile(code, CELL_FILE, "exec"), env)  # noqa: S102 (cells written above)
    except TimeoutError as error:
        return printed.getvalue() + traceback_text(error), "failed"
    return printed.getvalue().rstrip("\n"), "done"


def think(text):
    return {"kind": "think", "text": text}


def cell(code, agents=()):
    """A cell for agent() or turn() to run, in order, in that run's own namespace."""

    def run_in(env):
        env.update(repl_tools(agents))
        output, status = run(code, env)
        return {
            "kind": "cell",
            "code": code,
            "agents": list(agents),
            "output": output,
            "status": status,
        }

    return run_in


def final(value):
    return cell(f"FinalAnswer({value!r})")


def run_steps(steps, variables):
    env = {"FinalAnswer": final_answer, "course": course, "courses": courses}
    env.update(variables)
    return [step(env) if callable(step) else step for step in steps]


def cost_and_seconds(steps):
    """Made-up totals for these steps and every sub-agent under them."""
    cost = seconds = 0.0
    for step in steps:
        agents = step.get("agents", [])
        text = step.get("text") or step["code"]
        own = len(text) / CODE_CHARS_PER_SECOND + CELL_SECONDS
        seconds += THINK_SECONDS if step["kind"] == "think" else own
        seconds += max((agent["seconds"] for agent in agents), default=0.0)
        cost += STEP_COST + len(text) * COST_PER_CHAR
        cost += sum(agent["cost"] for agent in agents)
    return round(cost, 4), round(seconds, 1)


def result_of(steps, status):
    if status == "failed":
        return f"Failed: TimeoutError: {TIMEOUT}"
    if status == "exhausted":
        return f"Agent failed to produce a final answer within {len(steps)} iterations."
    return ast.literal_eval(steps[-1]["output"].removeprefix("FinalAnswer: "))


def agent(task, steps, status="done", cost=None, seconds=None, **variables):
    steps = run_steps(steps, variables)
    made_up_cost, made_up_seconds = cost_and_seconds(steps)
    return {
        "kind": "agent",
        "task": task,
        "status": status,
        "namespace": "root",
        "drive": 1,
        "steps": steps,
        "result": result_of(steps, status),
        "cost": made_up_cost if cost is None else cost,
        "seconds": made_up_seconds if seconds is None else seconds,
    }


def turn(prompt, steps, answer, cost=None, seconds=None, **variables):
    steps = run_steps(steps, {"answer": answer, **variables})
    made_up_cost, made_up_seconds = cost_and_seconds(steps)
    return {
        "prompt": prompt,
        "steps": steps,
        "answer": answer,
        "outcome": "answered",
        "cost": made_up_cost if cost is None else cost,
        "seconds": made_up_seconds if seconds is None else seconds,
    }


def sky_chat():
    scattering = agent(
        "How does Rayleigh scattering depend on wavelength?",
        [
            think(
                "Air molecules (N₂, O₂) are about 0.3 nm across, far smaller than visible wavelengths, so Rayleigh scattering applies and intensity goes as 1/λ⁴. Compare the two ends of the visible range."
            ),
            cell("print(round((700 / 400) ** 4, 1))"),
            final(
                "Intensity goes as 1/λ⁴: 400 nm light scatters about 9.4× more than 700 nm light."
            ),
        ],
        cost=0.0061,
        seconds=4.2,
    )
    eye = agent(
        "Photopic eye sensitivity at 410 nm and 470 nm, as a ratio?",
        [
            cell(
                "eye = {410: 0.00121, 470: 0.09098}  # CIE 1924 photopic sensitivity\nprint(round(eye[470] / eye[410]))"
            ),
            final("The eye is about 75× more sensitive at 470 nm than at 410 nm."),
        ],
        cost=0.0034,
        seconds=2.9,
    )
    violet = agent(
        "Violet scatters more than blue. Why isn't the sky violet?",
        [
            think(
                "Two things to check: how much violet the sun sends, and how sensitive the eye is to it. The eye part is a lookup; hand it off."
            ),
            cell(
                'eye = subagent("Photopic eye sensitivity at 410 nm and 470 nm, as a ratio?")\nprint(eye)',
                [eye],
            ),
            think(
                "The solar spectrum also falls off below about 450 nm, and ozone absorbs some violet high up. With the eye's response, the scattered mix reads as blue."
            ),
            final(
                "Sunlight carries less violet than blue, ozone absorbs some of it, and the eye is about 75× less sensitive at 410 nm than at 470 nm, so the scattered mix looks blue."
            ),
        ],
        cost=0.0118,
        seconds=9.8,
    )
    sunset = agent(
        "Why are sunsets red?",
        [
            think(
                "At sunset the light's path through the air is much longer, so more of the blue is scattered out of the beam before it arrives. How much longer?"
            ),
            cell(
                "import math\nzenith = 1 / math.cos(math.radians(0))\nhorizon = 38  # Kasten-Young air mass at 90 degrees\nprint(horizon / zenith)"
            ),
            final(
                "At the horizon sunlight crosses about 38× more air than at noon, so most blue is scattered away before it reaches you, leaving red and orange."
            ),
        ],
        cost=0.0057,
        seconds=5.1,
    )
    steps = [
        think(
            "Three questions in one: how scattering depends on wavelength, why the sky isn't violet when violet scatters even more, and why sunsets turn red. One sub-agent each, then combine."
        ),
        cell(SKY_SPAWN, [scattering, violet, sunset]),
        think("All three are back and consistent. Write the answer."),
        cell("FinalAnswer(answer)"),
    ]
    prompt = "why is the sky blue?"
    sky = turn(prompt, steps, SKY_ANSWER, cost=0.0371, seconds=16.4)
    return {"id": "sky", "title": prompt, "turns": [sky]}


def theory_track():
    """The deep branch: six levels of sub-agents under the root."""
    enforced = agent(
        "Is MATH 301 enforced as a prerequisite for CS 341?",
        [
            cell('print(course("CS 341")["prereqs"], course("CS 341")["notes"])'),
            final(
                "No: registration checks only CS 201 and CS 221; MATH 301 is a recommendation."
            ),
        ],
    )
    cs341 = agent(
        "Look up CS 341.",
        [
            cell('print(course("CS 341"))'),
            think(
                "The catalog lists MATH 301 as recommended. Ask whether registration enforces it."
            ),
            cell(
                'enforced = subagent("Is MATH 301 enforced as a prerequisite for CS 341?")\nprint(enforced)',
                [enforced],
            ),
            final(
                "CS 341 Theory of Computation needs CS 201 and CS 221; MATH 301 is recommended, not enforced."
            ),
        ],
    )
    cs311 = agent(
        "Look up CS 311.",
        [think("CS 311 is Algorithms. Read its catalog entry and list what it needs.")],
        status="failed",
    )
    chain = agent(
        "Trace the prerequisite chain under CS 311 and CS 341.",
        [
            cell('cs341 = subagent("Look up CS 341.")\nprint(cs341)', [cs341]),
            cell('cs311 = subagent("Look up CS 311.")\nprint(cs311)', [cs311]),
            think(
                "The CS 311 lookup timed out. Its catalog entry is short, so read it directly instead of asking again."
            ),
            cell(
                'def chain(code):\n    return {p: chain(p) for p in course(code)["prereqs"]}\n\nprint(chain("CS 311"))'
            ),
            final(
                "CS 311 needs CS 221, CS 341 needs CS 201 and CS 221 (MATH 301 recommended), CS 221 needs CS 162 and CS 201, and both of those need CS 161."
            ),
        ],
    )
    complexity_lookup = agent(
        "Look up CS 431 and trace its prerequisite chain.",
        [
            cell('print(course("CS 431"))'),
            cell(
                'chain = subagent("Trace the prerequisite chain under CS 311 and CS 341.")\nprint(chain)',
                [chain],
            ),
            final(
                "CS 431 Computational Complexity runs only in spring and needs CS 311 and CS 341; beneath them sit CS 221, CS 201, CS 162 and CS 161."
            ),
        ],
    )
    complexity = agent(
        "Which complexity courses are there, and what does each need first?",
        [
            think(
                "Complexity is CS 431, and its prerequisites have prerequisites of their own. Have a sub-agent look it up and trace the chain."
            ),
            cell(
                'info = subagent("Look up CS 431 and trace its prerequisite chain.")\nprint(info)',
                [complexity_lookup],
            ),
            final(
                "CS 431 Computational Complexity (spring only), after CS 311 and CS 341; plan CS 161, CS 162, CS 201 and CS 221 before those."
            ),
        ],
    )
    algorithms = agent(
        "Which algorithms courses are there, and what does each need first?",
        [
            cell('print({c: course(c)["prereqs"] for c in ["CS 311", "CS 421"]})'),
            final(
                "CS 311 Algorithms after CS 221, then CS 421 Advanced Algorithms (autumn only)."
            ),
        ],
    )
    logic = agent(
        "Which logic courses are there, and what does each need first?",
        [
            cell('print({c: course(c)["prereqs"] for c in ["CS 461", "PHIL 270"]})'),
            final(
                "CS 461 Logic in Computer Science after CS 341; PHIL 270 Symbolic Logic needs nothing."
            ),
        ],
    )
    cryptography = agent(
        "Which cryptography courses are there, and what does each need first?",
        [
            cell('print(course("CS 451"))'),
            final(
                "CS 451 Cryptography (autumn only), after CS 311 and STAT 311 Probability."
            ),
        ],
    )
    offerings = agent(
        "In which terms do CS 421, CS 431, CS 451 and CS 461 run?",
        [
            cell(
                'print({c: course(c)["terms"] for c in ["CS 421", "CS 431", "CS 451", "CS 461"]})'
            ),
            final(
                "CS 421 and CS 451 run only in autumn, CS 431 only in spring, CS 461 in both."
            ),
        ],
    )
    areas = [algorithms, complexity, logic, cryptography]
    return agent(
        "Map the theory track: which courses, and what each needs first?",
        [
            think(
                "Theory here means four areas: algorithms, complexity, logic and cryptography. One sub-agent per area finds the courses and what they need."
            ),
            cell(
                'areas = ["algorithms", "complexity", "logic", "cryptography"]\nfound = run_all({a: anext(subagent().send(f"Which {a} courses are there, and what does each need first?")) for a in areas})\nfor area, answer in found.items():\n    print(f"{area}: {answer}")',
                areas,
            ),
            think(
                "Several of these look like once-a-year courses. Check their terms before anyone builds a plan on them."
            ),
            cell(
                'terms = subagent("In which terms do CS 421, CS 431, CS 451 and CS 461 run?")\nprint(terms)',
                [offerings],
            ),
            final(
                "CS 311 Algorithms and CS 341 Theory of Computation, then CS 431 Complexity (spring only); add CS 421 (autumn only), CS 451 Cryptography (autumn only, needs STAT 311) and CS 461 Logic; finish with the CS 499 thesis, after CS 431."
            ),
        ],
    )


def electives():
    """The wide branch: six departments asked at once, one of which runs out of turns."""
    picks = {
        "MATH": "MATH 301 Introduction to Proofs first, then MATH 340 Abstract Algebra and MATH 381 Combinatorics.",
        "PHIL": "PHIL 270 Symbolic Logic, then PHIL 345 Philosophy of Mathematics.",
        "STAT": "STAT 311 Probability (already core), then STAT 421 Information Theory.",
        "ECON": "ECON 351 Game Theory: proofs about strategies and equilibria.",
        "LING": "LING 340 Formal Languages: grammars and automata from the other side.",
    }
    departments = [
        agent(
            f"Which {department} courses would a theory-minded CS student enjoy?",
            [
                cell(
                    f'print({{c: course(c)["title"] for c in courses("{department}")}})'
                ),
                final(pick),
            ],
        )
        for department, pick in picks.items()
    ]
    physics = agent(
        "Which PHYS courses would a theory-minded CS student enjoy?",
        [
            cell('print(courses("PHYS"))'),
            cell('print(course("PHYS 324"))'),
            cell('print(course("PHYS 225")["prereqs"])'),
        ],
        status="exhausted",
    )
    return agent(
        "Which courses outside CS suit a student who loves theory?",
        [
            think(
                "Theory leans on proofs, logic, probability and algebra. Ask each nearby department at once."
            ),
            cell(
                'departments = ["MATH", "PHIL", "STAT", "ECON", "LING", "PHYS"]\npicks = run_all({d: anext(subagent().send(f"Which {d} courses would a theory-minded CS student enjoy?")) for d in departments})\nfor d, pick in picks.items():\n    print(d, "→", pick)',
                [*departments, physics],
            ),
            think(
                "Physics ran out of turns, and the other five give plenty. Proofs and algebra matter most; logic backs up CS 461."
            ),
            final(
                "MATH 301 Introduction to Proofs as early as it fits, then MATH 340 Abstract Algebra and MATH 381 Combinatorics; PHIL 270 Symbolic Logic; ECON 351 Game Theory if there's room."
            ),
        ],
    )


def year_check(year, autumn, spring):
    """One year of the plan checked; the year with CS 451 asks a schedule agent too."""
    terms = {"autumn": autumn, "spring": spring}
    steps = [
        cell(
            f'terms = {terms!r}\nprint({{t: [c for c in chosen if t not in course(c)["terms"]] for t, chosen in terms.items()}})'
        )
    ]
    if "CS 451" in autumn:
        schedule = agent(
            "Is CS 451 on the autumn schedule every year?",
            [
                cell('print(course("CS 451")["terms"])'),
                final("Yes: CS 451 runs every autumn and never in spring."),
            ],
        )
        steps += [
            think(
                "CS 451 runs once a year. Make sure the autumn slot is real before relying on it."
            ),
            cell(
                'every_autumn = subagent("Is CS 451 on the autumn schedule every year?")\nprint(every_autumn)',
                [schedule],
            ),
        ]
    steps.append(
        final(f"Year {year}: at most three courses a term, each in a term it runs.")
    )
    task = f"Check year {year}: autumn {', '.join(autumn)}; spring {', '.join(spring)}."
    return agent(task, steps)


def plan_checker(semesters, plan):
    years = enumerate(zip(semesters[::2], semesters[1::2]), 1)
    checks = [year_check(year, autumn, spring) for year, (autumn, spring) in years]
    return agent(
        f"Check this plan for prerequisites, load and term offerings:\n{plan}",
        [
            think(
                "Two checks: prerequisites across the whole plan, which is quick in Python, then load and offerings, one sub-agent per year."
            ),
            cell(f"semesters = {semesters!r}\n{CHECK_PREREQS}"),
            cell(CHECK_YEARS, checks),
            final(
                "The plan holds: every prerequisite comes at least a term earlier, no term has more than three of these courses, and each course sits in a term it runs."
            ),
        ],
    )


def degree_chat():
    # the checker's task quotes the plan, so work the plan out before building it
    env = {"course": course}
    plan, _ = run(SCHEDULE, env)
    semesters = env["semesters"]
    core = agent(
        "List the core courses every CS major must take.",
        [
            cell(
                'core = ["CS 161", "CS 162", "CS 201", "CS 221", "CS 311", "CS 351", "MATH 151", "MATH 152", "MATH 241", "STAT 311"]\nprint(len(core), "courses,", sum(course(c)["credits"] for c in core), "credits")'
            ),
            final(
                "Ten courses, 44 credits: CS 161, 162, 201, 221, 311 and 351, MATH 151, 152 and 241, and STAT 311."
            ),
        ],
    )
    years = "\n".join(
        f"- **Year {year}:** autumn {', '.join(autumn)}; spring {', '.join(spring)}"
        for year, (autumn, spring) in enumerate(zip(semesters[::2], semesters[1::2]), 1)
    )
    answer = f"""\
An eight-term plan that gets proofs in early and reaches complexity theory in the last two years. Fill each term to a full load with general-education courses.

{years}

- **Theory track.** CS 311 Algorithms and CS 341 Theory of Computation, then CS 431 Computational Complexity, which runs only in spring, and a senior thesis, CS 499, to finish. CS 421, CS 451 Cryptography and CS 461 Logic round it out; CS 421 and CS 451 run only in autumn.
- **Outside CS.** MATH 301 Introduction to Proofs as early as it fits, then MATH 340 Abstract Algebra and MATH 381 Combinatorics; PHIL 270 Symbolic Logic, the logic behind CS 461; and ECON 351 Game Theory.
- **Checked.** Every prerequisite comes at least a term earlier, no term has more than three of these courses, and each course sits in a term it runs."""
    steps = [
        think(
            "Four questions: what the major requires, which theory courses to aim for and what each needs first, which courses outside CS suit a theorist, and whether the result fits a normal load. Three sub-agents for the first three; I'll lay out the terms myself and have the plan checked."
        ),
        cell(DEGREE_SPAWN, [core, theory_track(), electives()]),
        think(
            "Place every course after its prerequisites, at most three of them a term, each in a term it runs."
        ),
        cell(SCHEDULE),
        cell(
            'check = subagent(f"Check this plan for prerequisites, load and term offerings:\\n{plan}")\nprint(check)',
            [plan_checker(semesters, plan)],
        ),
        think("The check passed. Write the plan."),
        cell("FinalAnswer(answer)"),
    ]
    prompt = "Plan a four-year CS degree for a student who loves theory"
    return {"id": "degree", "title": prompt, "turns": [turn(prompt, steps, answer)]}


def essay_grader(essay_id, rng, role):
    """One of the 3,000 graders: mostly one step, some count words, a few go wrong."""
    task = f"Grade essay {essay_id}."
    essay = " ".join(rng.choices(ESSAY_WORDS, k=rng.randint(*ESSAY_LENGTH)))
    count = cell('print(len(essay.split()), "words")')
    leaf = {"cost": round(rng.uniform(*GRADER_COST), 4)}
    leaf["seconds"] = round(rng.uniform(*GRADER_SECONDS), 1)
    if role == "failed":
        return agent(task, [count], "failed", essay=essay, **leaf)
    if role == "exhausted":
        steps = [count, cell("print(essay[:60])"), cell("print(essay[-60:])")]
        return agent(task, steps, "exhausted", essay=essay, **leaf)
    if role == "borderline":
        question = f"Second opinion on essay {essay_id}: B or C?"
        second = agent(
            question, [final("C: the evidence doesn't carry the argument.")], **leaf
        )
        return agent(
            task,
            [
                think(
                    "Between B and C: the argument holds but the evidence is thin. Ask a second grader."
                ),
                cell(f"second = subagent({question!r})\nprint(second)", [second]),
                cell("FinalAnswer(second)"),
            ],
        )
    letter = rng.choices(list(GRADE_WEIGHTS), weights=GRADE_WEIGHTS.values())[0]
    verdict = f"{letter}: {rng.choice(COMMENTS[letter])}"
    if role == "counted" and len(essay.split()) < MIN_WORDS:
        verdict = f"D: under the {MIN_WORDS}-word minimum ({len(essay.split())} words)."
    steps = [count, final(verdict)] if role == "counted" else [final(verdict)]
    return agent(task, steps, essay=essay, **leaf)


def essay_roles(rng):
    special = rng.sample(
        range(ESSAY_COUNT), FAILED_ESSAYS + EXHAUSTED_ESSAYS + BORDERLINE_ESSAYS
    )
    roles = [
        "counted" if rng.random() < COUNTED_SHARE else "plain"
        for _ in range(ESSAY_COUNT)
    ]
    for n in special[:FAILED_ESSAYS]:
        roles[n] = "failed"
    for n in special[FAILED_ESSAYS : FAILED_ESSAYS + EXHAUSTED_ESSAYS]:
        roles[n] = "exhausted"
    for n in special[FAILED_ESSAYS + EXHAUSTED_ESSAYS :]:
        roles[n] = "borderline"
    return roles


def essays_chat():
    rng = random.Random(SEED)
    ids = [f"{n:04d}" for n in range(1, ESSAY_COUNT + 1)]
    roles = zip(ids, essay_roles(rng))
    graders = [essay_grader(essay_id, rng, role) for essay_id, role in roles]
    # the answer and a thought quote what the root's cells print, so run them ahead
    spawn = run_steps(
        [cell(ESSAYS_SPAWN, graders), cell(ESSAYS_UNGRADED)], {"essays": ids}
    )
    letters = ast.literal_eval(spawn[0]["output"])
    ungraded = spawn[1]["output"].split(": ", 1)[1]
    short = sum(grader["result"].startswith("D: under") for grader in graders)
    answer = f"""\
Graded {sum(letters.get(grade, 0) for grade in GRADE_WEIGHTS):,} of {ESSAY_COUNT:,} essays against the rubric.

- **Grades.** {" · ".join(f"{grade}: {letters.get(grade, 0):,}" for grade in GRADE_WEIGHTS)}
- **Too short.** {short} essays were under the {MIN_WORDS}-word minimum and got a D whatever their content.
- **Borderline.** {BORDERLINE_ESSAYS} graders asked a second grader, and the second grade stands.
- **Need a person.** {letters["failed"]} graders timed out and {letters["out of turns"]} ran out of turns: essays {ungraded}."""
    steps = [
        think(
            "3,000 essays and one rubric. Each essay stands alone, so give every one its own grader and run them all at once, catching failures so one bad grader can't sink the batch."
        ),
        cell(ESSAYS_SPAWN, graders),
        think(
            f"{letters['failed']} graders failed and {letters['out of turns']} ran out of turns. List those essays for a person, then report the distribution."
        ),
        cell(ESSAYS_UNGRADED),
        cell("FinalAnswer(answer)"),
    ]
    prompt = "Grade these 3,000 essays against the rubric"
    chat_turn = turn(prompt, steps, answer, essays=ids)
    return {"id": "essays", "title": prompt, "turns": [chat_turn]}


def main():
    chats = [sky_chat(), degree_chat(), essays_chat()]
    text = json.dumps({"chats": chats}, ensure_ascii=False, separators=(",", ":"))
    OUT.write_text(text + "\n")


if __name__ == "__main__":
    main()
