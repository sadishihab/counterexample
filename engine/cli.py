"""Command-line entrypoint: `counterexample review --repo PATH --base main --head BRANCH`.

Responsible for parsing CLI arguments and orchestrating diff.py, mutate.py,
runner.py, and receipt.py into a single `review` command that produces a
Review Receipt for a pull request.

TODO: implement argument parsing and orchestration of the review pipeline.
"""


def main() -> None:
    """Entry point registered as the `counterexample` console script.

    TODO: implement the `review` subcommand and wire it to the engine pipeline.
    """
    raise NotImplementedError
