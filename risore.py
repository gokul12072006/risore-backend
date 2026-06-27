import typer
from rich.console import Console
from rich.markdown import Markdown

from src.modules.app_dev import handle_app_dev
from src.modules.daily_life import handle_daily_life
from src.modules.education import handle_education
from src.modules.fitness import handle_fitness
from src.modules.memory import memory
from src.modules.productivity import handle_productivity
from src.modules.recommendation import handle_recommendation
from src.modules.tech import handle_tech
from src.modules.video import handle_video
from src.modules.voice import speak
from src.rag_pipeline import answer_question

app = typer.Typer(
    name="Risore",
    help="Risore AI Assistant CLI - A powerful personal assistant for productivity, learning, tech, and more.",
    add_completion=False,
)
console = Console()


def print_response(response: str, use_voice: bool = False):
    console.print(Markdown(response))
    if use_voice:
        speak(response)


@app.command()
def chat(
    prompt: str = typer.Argument(None, help="Your message to Risore"),
    voice: bool = typer.Option(False, "--voice", help="Enable voice responses"),
):
    """General conversation with Risore."""
    if prompt:
        console.print("[bold blue]Risore:[/bold blue]")
        print_response(answer_question(prompt), voice)
    else:
        console.print(
            "[bold green]Starting interactive chat... (Type 'exit' to quit)[/bold green]"
        )
        chat_history = []
        while True:
            try:
                user_input = console.input("[bold yellow]You:[/bold yellow] ")
                if user_input.lower() in ["exit", "quit"]:
                    break

                history_str = "\n".join(chat_history[-8:])

                console.print("[bold blue]Risore:[/bold blue]")
                response = answer_question(user_input, history=history_str)
                print_response(response, voice)

                chat_history.append(f"User: {user_input}")
                chat_history.append(f"Risore: {response}")

            except (KeyboardInterrupt, EOFError):
                break


@app.command()
def fitness(prompt: str = typer.Argument(..., help="Your fitness question")):
    """Get science-backed fitness and nutrition advice."""
    console.print("[bold blue]Risore (Fitness):[/bold blue]")
    print_response(handle_fitness(prompt))


@app.command()
def tech(prompt: str = typer.Argument(..., help="Your programming or tech question")):
    """Get expert programming and technology support."""
    console.print("[bold blue]Risore (Tech):[/bold blue]")
    print_response(handle_tech(prompt))


@app.command()
def daily(prompt: str = typer.Argument(..., help="Your daily life question")):
    """Get help with daily planning, reminders, and habit building."""
    console.print("[bold blue]Risore (Daily Life):[/bold blue]")
    print_response(handle_daily_life(prompt))


@app.command()
def productivity(prompt: str = typer.Argument(..., help="Your productivity question")):
    """Get actionable advice on task planning and time management."""
    console.print("[bold blue]Risore (Productivity):[/bold blue]")
    print_response(handle_productivity(prompt))


@app.command()
def recommend(
    prompt: str = typer.Argument(..., help="What do you want a recommendation for?")
):
    """Get intelligent product recommendations and comparisons."""
    console.print("[bold blue]Risore (Recommendation):[/bold blue]")
    print_response(handle_recommendation(prompt))


@app.command()
def study(prompt: str = typer.Argument(..., help="Your education question")):
    """Advanced learning companion for academic subjects and skills."""
    console.print("[bold blue]Risore (Education):[/bold blue]")
    print_response(handle_education(prompt))


@app.command()
def app_dev(prompt: str = typer.Argument(..., help="Your app development question")):
    """Guidance on mobile, web, and UI/UX development."""
    console.print("[bold blue]Risore (App Dev):[/bold blue]")
    print_response(handle_app_dev(prompt))


@app.command()
def video(prompt: str = typer.Argument(..., help="Your video creation question")):
    """Assistance with script writing, storyboarding, and video editing."""
    console.print("[bold blue]Risore (Video):[/bold blue]")
    print_response(handle_video(prompt))


@app.command()
def memory_set(key: str, value: str):
    """Store a personal preference in Risore's memory."""
    memory.update_preference(key, value)
    console.print(f"[bold green]Saved preference:[/bold green] {key} = {value}")


if __name__ == "__main__":
    app()
