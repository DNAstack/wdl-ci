import click
from wdlci.cli.generate_config import generate_config_handler
from wdlci.cli.lint import lint_handler
from wdlci.cli.detect_changes import detect_changes_handler
from wdlci.cli.submit import submit_handler
from wdlci.cli.monitor import monitor_handler
from wdlci.cli.cleanup import cleanup_handler
from wdlci.utils.ordered_group import OrderedGroup

remove_option = click.option(
    "--remove",
    "-r",
    is_flag=True,
    default=False,
    show_default=True,
    help="Remove workflows and tasks that are no longer found",
)

update_digests_option = click.option(
    "--update-digests",
    "-u",
    is_flag=True,
    default=False,
    show_default=True,
    help="Update the task digests for tasks that completed their tests successfully",
)

suppress_lint_errors_option = click.option(
    "--suppress-lint-errors",
    "-s",
    is_flag=True,
    default=False,
    show_default=True,
    help="Do not exit upon encountering a linting warning or error",
)


@click.group(cls=OrderedGroup)
def main():
    """Validate and test WDL workflows"""


@main.command
@remove_option
def generate_config(**kwargs):
    """Generate or update the WDL CI config file.

    If the config file already exists, new workflows and tasks will be added. Existing workflows and tasks (including tests) will not be updated or removed.
    """

    generate_config_handler(kwargs)


@main.command
@suppress_lint_errors_option
def lint(**kwargs):
    """Lint a WDL workflow"""

    lint_handler(kwargs)


@main.command
def detect_changes(**kwargs):
    """Detect updated tasks within a workflow"""

    detect_changes_handler(kwargs)


@main.command(hidden=True)
@remove_option
def update_task_digests(**kwargs):
    """Update task digests in the config file. This should only be called by the github action"""

    generate_config_handler(kwargs, update_task_digests=True)


@main.command
@click.option(
    "--all", "-a", is_flag=True, default=False, show_default=True, help="run all tests"
)
def submit(**kwargs):
    """Submit workflow runs to Workbench using test inputs"""

    submit_handler(kwargs)


@main.command
@update_digests_option
def monitor(**kwargs):
    """Monitor test runs and validate output"""

    monitor_handler(kwargs)


@main.command
def cleanup(**kwargs):
    """Clean Workbench namespace of transient artifacts"""

    cleanup_handler(kwargs)
