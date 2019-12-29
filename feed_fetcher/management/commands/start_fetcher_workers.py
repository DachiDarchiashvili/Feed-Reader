from django.core.management.base import BaseCommand, CommandError
from feed_fetcher.main import main


class Command(BaseCommand):
    help = 'Start Async Workers'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        """

        :param args:
        :param options:
        :return:
        """

        try:
            main()
        except Exception as e:
            raise CommandError(f'{e}')
