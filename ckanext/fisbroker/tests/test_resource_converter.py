# coding: utf-8

import logging
from ckanext.fisbroker.fisbroker_resource_converter import FISBrokerResourceConverter

log = logging.getLogger(__name__)

class TestResourceConverter(object):

    def _assert_equal(self, actual, expected):
        log.debug("expected: %s", expected)
        log.debug("actual:   %s", actual)
        assert expected == actual

    def test_convert_getcapabilities(self):
        """An incoming FIS-Broker service URL with URL parameters containing 'request=GetCapabilities'
           should be returned unchanged."""

        url = 'https://fbinter.stadt-berlin.de/fb/wfs/data/senstadt/s_boden_wfs1_2015?request=getcapabilities&service=wfs&version=2.0.0'
        resource = { 'url': url }
        converter = FISBrokerResourceConverter()
        converted_resource = converter.convert_resource(resource)
        
        self._assert_equal(converted_resource['url'], url)

    def test_plain_service_wfs_url(self):
        """An incoming FIS-Broker WFS service URL without URL parameters containing 'request=GetCapabilities'
           should be concatenated with said URL parameters."""

        url = 'https://fbinter.stadt-berlin.de/fb/wfs/data/senstadt/s_boden_wfs1_2015'
        resource = { 'url': url }
        converter = FISBrokerResourceConverter()
        converted_resource = converter.convert_resource(resource)
        
        self._assert_equal('{}{}'.format(url, "?service=wfs&{}".format(FISBrokerResourceConverter.getcapabilities_suffix())), converted_resource['url'])

    def test_plain_service_wms_url(self):
        """An incoming FIS-Broker WMS service URL without URL parameters containing 'request=GetCapabilities'
           should be concatenated with said URL parameters."""

        url = 'https://fbinter.stadt-berlin.de/fb/wms/senstadt/wmsk_02_14_04gwtemp_60m'
        resource = { 'url': url }
        converter = FISBrokerResourceConverter()
        converted_resource = converter.convert_resource(resource)
        
        self._assert_equal('{}{}'.format(url, "?service=wms&{}".format(FISBrokerResourceConverter.getcapabilities_suffix())), converted_resource['url'])

    def test_atom_feed_url(self):
        url = 'https://fbinter.stadt-berlin.de/fb/feed/senstadt/a_SU_LOR'
        resource = { 'url': url }
        converter = FISBrokerResourceConverter()
        converted_resource = converter.convert_resource(resource)

        self._assert_equal(converted_resource['url'], url)
        self._assert_equal(converted_resource['name'], "Atom Feed")
        self._assert_equal(converted_resource['description'], "Atom Feed")
        self._assert_equal(converted_resource['format'], "Atom")

    def test_service_page_url(self):
        url = 'https://fbinter.stadt-berlin.de/fb?loginkey=showMap&mapId=k01_11_07naehr2015@senstadt'
        resource = { 'url': url }
        converter = FISBrokerResourceConverter()
        converted_resource = converter.convert_resource(resource)

        self._assert_equal(converted_resource['url'], url)
        self._assert_equal(converted_resource['name'], "Serviceseite im FIS-Broker")
        self._assert_equal(converted_resource['description'], "Serviceseite im FIS-Broker")
        self._assert_equal(converted_resource['format'], "HTML")


    def test_arbitrary_url_with_description(self):
        url = 'https://fbinter.stadt-berlin.de/fb_daten/beschreibung/umweltatlas/datenformatbeschreibung/Datenformatbeschreibung_kriterien_zur_bewertung_der_bodenfunktionen2015.pdf'
        description = 'Technische Beschreibung'
        res_format = 'PDF'
        resource = {
            'url': url ,
            'name': description ,
            'description': description ,
            'format': res_format
        }
        converter = FISBrokerResourceConverter()
        converted_resource = converter.convert_resource(resource)

        self._assert_equal(converted_resource['name'], description)
        self._assert_equal(converted_resource['description'], description)
        self._assert_equal(converted_resource['format'], res_format)
        self._assert_equal(converted_resource['url'], url)

    def test_arbitrary_url_without_description(self):
        url = 'https://fbinter.stadt-berlin.de/fb_daten/beschreibung/umweltatlas/datenformatbeschreibung/Datenformatbeschreibung_kriterien_zur_bewertung_der_bodenfunktionen2015.pdf'
        res_format = 'PDF'
        resource = {
            'url': url ,
            'name': 'Technische Beschreibung' ,
            'format': res_format
        }
        converter = FISBrokerResourceConverter()
        converted_resource = converter.convert_resource(resource)

        self._assert_equal(converted_resource, None)

    def test_build_wms_resource(self):
        """Build WMS service resource from a WMS service URL."""

        url = 'https://fbinter.stadt-berlin.de/fb/wms/senstadt/wmsk_02_14_04gwtemp_60m'
        resource = { 'url': url }
        converter = FISBrokerResourceConverter()
        service_resource = converter.build_service_resource(resource)

        self._assert_equal(service_resource['url'], "{}?service=wms&{}".format(url, FISBrokerResourceConverter.getcapabilities_suffix()))
        self._assert_equal(service_resource['name'], "WMS Service")
        self._assert_equal(service_resource['description'], "WMS Service")
        self._assert_equal(service_resource['format'], "WMS")

    def test_build_wfs_resource(self):
        """Build WFS service resource from a WFS service URL."""

        url = 'https://fbinter.stadt-berlin.de/fb/wfs/data/senstadt/s_boden_wfs1_2015'
        resource = { 'url': url }
        converter = FISBrokerResourceConverter()
        service_resource = converter.build_service_resource(resource)

        self._assert_equal(service_resource['url'], "{}?service=wfs&{}".format(url, FISBrokerResourceConverter.getcapabilities_suffix()))
        self._assert_equal(service_resource['name'], "WFS Service")
        self._assert_equal(service_resource['description'], "WFS Service")
        self._assert_equal(service_resource['format'], "WFS")

    def test_atom_feed_resource_returned_unchanged(self):
        url = 'https://fbinter.stadt-berlin.de/fb/feed/senstadt/a_SU_LOR'
        resource = { 'url': url }
        converter = FISBrokerResourceConverter()
        converted_resource = converter.build_service_resource(resource)

        self._assert_equal(converted_resource['url'], url)
        self._assert_equal(len(converted_resource), 1)

    def test_normalize_url(self):
        url1 = 'https://fbinter.stadt-berlin.de/fb/wfs/data/senstadt/s_boden_wfs1_2015?request=getcapabilities&service=wfs&version=2.0.0'
        url2 = 'https://fbinter.stadt-berlin.de/fb/wfs/data/senstadt/s_boden_wfs1_2015?service=wfs&version=2.0.0&request=GetCapabilities'

        converter = FISBrokerResourceConverter()
        self._assert_equal(converter.normalize_url(url1), converter.normalize_url(url2))