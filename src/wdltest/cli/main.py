import click

@click.group
def main():
    """Validate and test WDL workflows"""

@main.command
def lint():
    """TODO: lint a WDL workflow"""

@main.command
def detect_changes():
    """TODO: detect updated tasks within a workflow"""

@main.command
def submit():
    """TODO: Submit task tests to WDL executor or delegator"""

@main.command
def monitor():
    """TODO: Monitor tests and assert outputs of finshed tasks"""
