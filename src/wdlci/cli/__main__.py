import click
from wdlci.cli.detect_changes import detect_changes_handler
from wdlci.cli.submit import submit_handler
from wdlci.cli.monitor import monitor_handler

@click.group
def main():
    """Validate and test WDL workflows"""

@main.command
def lint():
    """TODO: lint a WDL workflow"""

@main.command
def detect_changes():
    """detect updated tasks within a workflow"""

    detect_changes_handler()

@main.command
@click.option('--all', '-a', is_flag=True, default=False, show_default=True, help="run all tests")
def submit(**kwargs):
    """Submit workflow runs to Workbench using test inputs"""

    submit_handler(kwargs)

@main.command
def monitor(**kwargs):
    """Monitor test workflow runs and assert outputs of finshed tasks"""

    monitor_handler(kwargs)
