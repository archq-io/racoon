from rich.console import Console
from rich.progress import Progress
from rich.markdown import Markdown

class ConsoleOutput:
    def __init__(self):
        self.__console = Console()
        self.__status = None

    def manifest_parsing_start(self, name):
        if self.__status is None:
            self.__status = self.__console.status('🦝 Running manifest "{}"'.format(name))
            self.__status.start()
        self.__console.print('🔸 Running manifest "{}"'.format(name))

    def manifest_parsing_end(self, name):
        if self.__status is not None:
            self.__status.stop()
            self.__status = None
        self.__console.print('✅ Manifest "{}" succeeded...'.format(name))

    def file_start(self, src, dst, save_file):
        if save_file:
            self.__console.print('📄 Copying file from {} to {}'.format(src, dst))
            return
        self.__console.print('📄 Loading file from {}'.format(src))

    def file_end(self, src, dst, save_file, error):
        if error:
            if save_file:
                self.__console.print('❌ Error: Could not copy file {}'.format(src))
                return
            self.__console.print('❌ Error: Could not load file {}'.format(src))

    def verify_start(self, file_name):
        pass

    def verify_end(self, file_name, error):
        if error:
            self.__console.print('❌ Error: File {} validation failed'.format(file_name))
