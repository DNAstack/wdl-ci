import click
from wdlci.cli.detect_changes import detect_changes_handler
from wdlci.cli.submit import submit_handler
from wdlci.cli.monitor import monitor_handler
from wdlci.cli.cleanup import cleanup_handler
from wdlci.utils.ordered_group import OrderedGroup

@click.group(cls=OrderedGroup)
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
    """Monitor test runs and validate output"""

    monitor_handler(kwargs)

@main.command
def cleanup(**kwargs):
    """Clean Workbench namespace of transient artifacts"""

    cleanup_handler(kwargs)
