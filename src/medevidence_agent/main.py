import typer

from medevidence_agent.config import settings
from medevidence_agent.workflow import run_workflow


app = typer.Typer(add_completion=False)


@app.command()
def main(question: str) -> None:
    """Run the MedEvidence Agent workflow for a clinical question."""
    run_workflow(question, settings, verbose=True)


if __name__ == "__main__":
    app()
