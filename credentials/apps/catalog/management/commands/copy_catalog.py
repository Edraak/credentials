""" Copy catalog data from Discovery. """

import logging

from django.contrib.sites.models import Site
from django.core.management import BaseCommand

from credentials.apps.catalog.utils import parse_program
from credentials.apps.core.models import SiteConfiguration

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Copy catalog data from Discovery'

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument(
            '--page-size',
            action='store',
            type=int,
            default=None,
            help='The maximum number of catalog items to request at once.'
        )

    def handle(self, *args, **options):
        page_size = options.get('page_size')

        for site in Site.objects.all():
            site_configs = SiteConfiguration.objects.filter(site=site)
            site_config = site_configs.get() if site_configs.exists() else None
            if not site_config or not site_config.catalog_api_url:
                logger.info('Skipping site {}. No configuration.'.format(site.domain))
                continue

            logger.info('Copying catalog data for site {}'.format(site.domain))
            client = site_config.catalog_api_client
            Command.fetch_programs(site, client, page_size=page_size)

    @staticmethod
    def fetch_programs(site, client, page_size=None):
        next_page = 1
        while next_page:
            programs = client.programs.get(exclude_utm=1, page=next_page, page_size=page_size)
            for program in programs['results']:
                logger.info('Copying program "{}"'.format(program['title']))
                parse_program(site, program)
            next_page = next_page + 1 if programs['next'] else None
