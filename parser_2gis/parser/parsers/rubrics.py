from __future__ import annotations
import base64

import json
import re
import time
from typing import TYPE_CHECKING

import urllib3

from ...common import wait_until_finished
from ...logger import logger
from .main import MainParser

if TYPE_CHECKING:
    from ...chrome.dom import DOMNode
    from ...writer import FileWriter


class RubricsParser(MainParser):
    """Parser for the list of categories (rubrics) provided by 2GIS with the tab "In building".

    URL pattern for such cases: https://2gis.<domain>/<city_id>/rubrics
    """

    @staticmethod
    def url_pattern():
        """URL pattern for the parser."""
        return r'https?://2gis\.[^/]+/[^/]+/rubrics'

    @wait_until_finished(timeout=5, throw_exception=False)
    def _get_links(self) -> list[DOMNode]:
        """Extracts specific DOM node links from current DOM snapshot."""
        def valid_link(node: DOMNode) -> bool:
            if node.local_name == 'a' and 'href' in node.attributes:
                link_match = re.match(r'.+/rubrics/[^/]', node.attributes['href'])
                return bool(link_match)
            return False

        dom_tree = self._chrome_remote.get_document()
        return dom_tree.search(valid_link)


    def parse(self, writer: FileWriter) -> None:
        """Parse URL with organizations.

        Args:
            writer: Target file writer.
        """
        # Go URL
        self._chrome_remote.navigate(self._url, referer='https://google.com', timeout=120)

        # Document loaded, get its response
        responses = self._chrome_remote.get_responses(timeout=5)
        if not responses:
            logger.error('Ошибка получения ответа сервера.')
            return
        document_response = responses[0]

        # Handle 404
        assert document_response['mimeType'] == 'text/html'
        if document_response['status'] == 404:
            logger.warn('Сервер вернул сообщение "Точных совпадений нет / Не найдено".')

            if self._options.skip_404_response:
                return

        # Parsed records
        collected_records = 0

        # Already visited links
        visited_links: set[str] = set()

        # Get new links
        @wait_until_finished(timeout=5, throw_exception=False)
        def get_unique_links() -> list[DOMNode]:
            links = self._get_links()
            link_addresses = set(x.attributes['href'] for x in links) - visited_links
            visited_links.update(link_addresses)
            return [x for x in links if x.attributes['href'] in link_addresses]
        
        # while True:
        self._wait_requests_finished()

        links = get_unique_links()
