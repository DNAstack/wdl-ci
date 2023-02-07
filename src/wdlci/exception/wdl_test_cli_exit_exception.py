from wdlci.exception.wdl_test_cli_exception import WdlTestCliException


class WdlTestCliExitException(WdlTestCliException):
    def __init__(self, message, exit_code):
        super().__init__(message)
        self.exit_code = exit_code
