# coding: utf-8
"""Tests for plugin.py."""

import logging
import os
from nose.tools import assert_raises

from ckan.logic import get_action

from ckanext.harvest.model import (
    HarvestObject,
)

from ckanext.spatial.harvesters.base import SpatialHarvester
from ckanext.spatial.model import ISODocument

from ckanext.fisbroker.plugin import (
    FisbrokerPlugin,
    marked_as_opendata,
    marked_as_service_resource,
    filter_tags,
    extract_license_and_attribution,
    extract_reference_dates,
    extract_url,
    extract_preview_markup,
    extras_as_list
)
from ckanext.fisbroker.tests import FisbrokerTestBase, _assert_equal

LOG = logging.getLogger(__name__)

class TestTransformationHelpers(FisbrokerTestBase):
    '''Tests for transformation helper methods used in get_package_dict. To see how CSW documents are mapped
       to ISO, check `ckanext.spatial.model.harvested_metadata.py/ISODocument`.'''

    def _open_xml_fixture(self, xml_filename):
        xml_filepath = os.path.join(os.path.dirname(__file__),
                                    'xml',
                                    xml_filename)
        with open(xml_filepath, 'rb') as f:
            xml_string_raw = f.read()

        return xml_string_raw

    def _csw_resource_data_dict(self, dataset_name):
        '''Return an example open data dataset as expected as input
           to get_package_dict().'''

        xml_string = self._open_xml_fixture(dataset_name)
        iso_document = ISODocument(xml_string)
        iso_values = iso_document.read_values()
        base_harvester = SpatialHarvester()
        source = self._create_source()
        obj = HarvestObject(
            source=source,
        )
        obj.save()
        package_dict = base_harvester.get_package_dict(iso_values, obj)

        data_dict = {
            'package_dict': package_dict ,
            'iso_values': iso_values
        }
        return data_dict

    def _resource_list(self):
        return [
            {
                u'description': u'WFS Service',
                u'format': u'WFS',
                u'id': u'0776059c-b9a7-4b9f-9cae-7c7ff0ca9f86',
                u'internal_function': u'api',
                u'main': u'True',
                u'name': u'WFS Service',
                u'package_id': u'4e35031f-39ee-45bd-953f-f27398791ba1',
                u'position': 0,
                u'resource_locator_function': u'information',
                u'url': u'https://fbinter.stadt-berlin.de/fb/wfs/data/senstadt/s01_11_07naehr2015?request=getcapabilities&service=wfs&version=2.0.0',
            },
            {
                u'description': u'Serviceseite im FIS-Broker',
                u'format': u'HTML',
                u'id': u'dd7c056a-227b-453e-a2d0-516bf3fb1611',
                u'internal_function': u'web_interface',
                u'main': u'False',
                u'name': u'Serviceseite im FIS-Broker',
                u'package_id': u'4e35031f-39ee-45bd-953f-f27398791ba1',
                u'position': 1,
                u'resource_locator_function': u'information',
                u'url': u'https://fbinter.stadt-berlin.de/fb?loginkey=alphaDataStart&alphaDataId=s01_11_07naehr2015@senstadt',
            },
            {
                u'description': u'Inhaltliche Beschreibung',
                u'format': u'HTML',
                u'id': u'1e368892-d95b-459b-a065-ec19462f31d1',
                u'internal_function': u'documentation',
                u'main': u'False',
                u'name': u'Inhaltliche Beschreibung',
                u'package_id': u'4e35031f-39ee-45bd-953f-f27398791ba1',
                u'position': 2,
                u'resource_locator_function': u'information',
                u'url': u'https://www.stadtentwicklung.berlin.de/umwelt/umweltatlas/dd11107.htm',
            },
            {
                u'description': u'Technische Beschreibung',
                u'format': u'PDF',
                u'id': u'9737084b-b3e6-412d-a220-436a98d815cc',
                u'internal_function': u'documentation',
                u'main': u'False',
                u'name': u'Technische Beschreibung',
                u'package_id': u'4e35031f-39ee-45bd-953f-f27398791ba1',
                u'position': 3,
                u'resource_locator_function': u'information',
                u'url': u'https://fbinter.stadt-berlin.de/fb_daten/beschreibung/umweltatlas/datenformatbeschreibung/Datenformatbeschreibung_kriterien_zur_bewertung_der_bodenfunktionen2015.pdf',
            }
        ]

    def test_filter_tags(self):
        '''Check if all tags from `to_remove` are removed from the
           output tag list. In case of duplicate tags, all occurrences of
           a tag should be removed, not just the first one.'''
        to_remove = [
            'open data', # that's a duplicate; both occurrences should be removed
            'Berlin',
            'Hamburg', # that's not in the original tag list, shouldn't change anything
            'Boden',
            u'N\xe4hrstoffversorgung',
        ]
        data_dict = self._csw_resource_data_dict('wfs-open-data.xml')
        simple_tag_list = data_dict['iso_values']['tags']
        complex_tag_list = data_dict['package_dict']['tags']
        expected_result = [
            {'name': 'inspireidentifiziert'},
            {'name': 'opendata'},
            {'name': 'Sachdaten'},
            {'name': 'Umweltatlas'},
            {'name': 'Bodengesellschaft'},
            {'name': 'Ausgangsmaterial'},
            {'name': 'Oberboden'},
            {'name': 'Unterboden'},
            {'name': 'KAKeff'},
            {'name': 'pH-Wert'},
            {'name': 'Bodenart'},
            {'name': u'Basens\xe4ttigung'},
            {'name': u'B\xf6den'},
            {'name': 'infoFeatureAccessService'},
        ]
        filter_tags(to_remove, simple_tag_list, complex_tag_list)
        _assert_equal(complex_tag_list, expected_result)

    def test_is_open_data(self):
        '''Test for correctly assigning Open Data status if the dataset
           has been marked as such.'''

        data_dict = self._csw_resource_data_dict('wfs-open-data.xml')
        assert marked_as_opendata(data_dict)

    def test_is_close_data(self):
        '''Test for correctly assigning Closed Data status if the dataset
           has not been marked as Open Data.'''

        data_dict = self._csw_resource_data_dict('wfs-closed-data.xml')
        assert not marked_as_opendata(data_dict)

    def test_skip_on_closed_data_resource(self):
        '''Test if get_package_dict() returns 'skip' for a closed data
           CSW resource.'''

        data_dict = self._csw_resource_data_dict('wfs-closed-data.xml')
        _assert_equal(FisbrokerPlugin().get_package_dict(self.context, data_dict), 'skip')

    def test_is_service_resource(self):
        '''Test to check if a dataset is correctly classified as a service
           resource.'''

        data_dict = self._csw_resource_data_dict('wfs-open-data.xml')
        _assert_equal(marked_as_service_resource(data_dict), True)

    def test_is_not_service_resource(self):
        '''Test to check if a dataset is correctly classified as not being service
           resource.'''

        data_dict = self._csw_resource_data_dict('dataset-open-data.xml')
        _assert_equal(marked_as_service_resource(data_dict), False)

    def test_skip_on_dataset_resource(self):
        '''Test if get_package_dict() returns 'skip' for a dataset
           CSW resource (as opposed to a service resource).'''

        data_dict = self._csw_resource_data_dict('dataset-open-data.xml')
        _assert_equal(FisbrokerPlugin().get_package_dict(self.context, data_dict), 'skip')

    def test_skip_on_missing_responsible_organisation(self):
        '''Test if get_package_dict() returns 'skip' for a service resource
           without any information of the responsible party.'''

        data_dict = self._csw_resource_data_dict('wfs-no-responsible-party.xml')
        _assert_equal(FisbrokerPlugin().get_package_dict(self.context, data_dict), 'skip')

    def test_skip_on_missing_org_name(self):
        '''Test if get_package_dict() returns 'skip' for a service resource
           without an organisation name in the responsible party information.'''

        data_dict = self._csw_resource_data_dict('wfs-no-org-name.xml')
        _assert_equal(FisbrokerPlugin().get_package_dict(self.context, data_dict), 'skip')

    def test_skip_on_missing_email(self):
        '''Test if get_package_dict() returns 'skip' for a service resource
           without an email in the responsible party information.'''

        data_dict = self._csw_resource_data_dict('wfs-no-email.xml')
        _assert_equal(FisbrokerPlugin().get_package_dict(self.context, data_dict), 'skip')

    def test_skip_on_missing_license_info(self):
        '''Test if get_package_dict() returns 'skip' for a service resource
           without parseable license information.'''

        data_dict = self._csw_resource_data_dict('wfs-no-license.xml')
        _assert_equal(FisbrokerPlugin().get_package_dict(self.context, data_dict), 'skip')

    def test_fix_bad_dl_de_id(self):
        '''Test if incorrect license id for DL-DE-BY has been corrected.'''

        data_dict = {
            'iso_values': {
                'limitations-on-public-access': [
                    '{ "id": "dl-de-by-2-0" , "name": " Datenlizenz Deutschland - Namensnennung - Version 2.0 ", "url": "https://www.govdata.de/dl-de/by-2-0", "quelle": "Umweltatlas Berlin / [Titel des Datensatzes]" }'
                ]
            }
        }
        license_and_attribution = extract_license_and_attribution(data_dict)
        _assert_equal(license_and_attribution['license_id'], "dl-de-by-2.0")

    def test_skip_on_missing_release_date(self):
        '''Test if get_package_dict() returns 'skip' for a service resource
           without a release date.'''

        data_dict = self._csw_resource_data_dict('wfs-no-release-date.xml')
        # LOG.info("iso_valalala: %s", data_dict['iso_values'])
        # assert False
        _assert_equal(FisbrokerPlugin().get_package_dict(self.context, data_dict), 'skip')

    def test_revision_interpreted_as_updated_creation_as_released(self):
        '''Test if a reference date of type `revision` is interpreted as
           `date_updated` and a date of type `creation` as `date_released`.
           `publication` should be ignored if `creation` was already present.'''

        creation = '1974-06-07'
        publication = '1994-05-03'
        revision = '2000-01-01'
        data_dict = {
            'iso_values': {
                'dataset-reference-date': [
                    {
                        'type': 'creation',
                        'value': creation,
                    } ,
                    {
                        'type': 'publication',
                        'value': publication,
                    } ,
                    {
                        'type': 'revision' ,
                        'value': revision,
                    } ,
                ]
            }
        }

        reference_dates = extract_reference_dates(data_dict)
        _assert_equal(reference_dates['date_released'], creation)
        _assert_equal(reference_dates['date_updated'], revision)

    def test_publication_interpreted_as_released(self):
        '''Test if a reference date of type `publication` is interpreted as
           `date_released` if `creation` is no present.'''

        publication = '1994-05-03'
        revision = '2000-01-01'
        data_dict = {
            'iso_values': {
                'dataset-reference-date': [
                    {
                        'type': 'publication',
                        'value': publication,
                    } ,
                    {
                        'type': 'revision',
                        'value': revision,
                    },
                ]
            }
        }

        reference_dates = extract_reference_dates(data_dict)
        _assert_equal(reference_dates['date_released'], publication)
        _assert_equal(reference_dates['date_updated'], revision)

    def test_date_updated_as_fallback_for_date_released(self):
        '''Test that, if no `date_released` could be extracted, the
           value of `date_updated` is used as a fallback.'''

        revision = '2000-01-01'
        data_dict = {
            'iso_values': {
                'dataset-reference-date': [
                    {
                        'type': 'revision',
                        'value': revision,
                    },
                ]
            }
        }

        reference_dates = extract_reference_dates(data_dict)
        _assert_equal(reference_dates['date_released'], revision)
        _assert_equal(reference_dates['date_updated'], revision)

    def test_web_interface_resource_picked_as_url(self):
        '''Test that the resource marked as `web_interface` is picked as the
           dataset's `url` metadatum.'''

        resources = self._resource_list()
        url = extract_url(resources)
        _assert_equal(
            url, u'https://fbinter.stadt-berlin.de/fb?loginkey=alphaDataStart&alphaDataId=s01_11_07naehr2015@senstadt')

    def test_api_resource_as_fallback_for_url(self):
        '''Test that the resource marked as `api` is picked as the
           dataset's `url` metadatum, if no `web_interface` is present.'''

        resources = self._resource_list()
        resources = list(filter(lambda x: x.get('internal_function') != 'web_interface', resources))
        url = extract_url(resources)
        _assert_equal(
            url, u'https://fbinter.stadt-berlin.de/fb/wfs/data/senstadt/s01_11_07naehr2015?request=getcapabilities&service=wfs&version=2.0.0')

    def test_no_web_interface_or_api_means_no_url(self):
        '''Test that no url is picked if neither `web_interface` nor `api` is present.'''

        resources = self._resource_list()
        resources = list(filter(lambda x: x.get('internal_function') != 'web_interface', resources))
        resources = list(filter(lambda x: x.get('internal_function') != 'api', resources))
        url = extract_url(resources)
        _assert_equal(url, None)

    def test_build_preview_graphic_markup(self):
        '''Test that, for a dataset that has an MD_BrowseGraphic named 'Vorschaugrafik',
           the correct image markdown is generated.'''
        data_dict = self._csw_resource_data_dict('wfs-open-data.xml')

        preview_markup = extract_preview_markup(data_dict)
        _assert_equal(
            preview_markup, u"![Vorschaugrafik zu Datensatz 'Nährstoffversorgung des Oberbodens 2015 (Umweltatlas)'](https://fbinter.stadt-berlin.de/fb_daten/vorschau/sachdaten/svor_default.gif)")

    def test_no_preview_graphic_wrong_name(self):
        '''Test that, for a dataset that has a MD_BrowseGraphic but not one named 'Vorschaugrafik',
           no image is generated.'''
        data_dict = self._csw_resource_data_dict('wfs-no-preview_1.xml')
        preview_markup = extract_preview_markup(data_dict)
        _assert_equal(preview_markup, None)

    def test_no_preview_graphic_no_image(self):
        '''Test that, for a dataset that has doesn't have any graphics,
           no image is generated.'''

        data_dict = self._csw_resource_data_dict('wfs-no-preview_2.xml')
        preview_markup = extract_preview_markup(data_dict)
        _assert_equal(preview_markup, None)

    def test_complex_extras_become_json(self):
        '''Test that converting extra-dicts to list of dicts works, 
           including the conversion of complex values to JSON strings.'''

        extras_dict = {
            'foo': 'bar' ,
            'inners': [
                'mercury', 'venus', 'earth', 'mars'
            ] ,
            'holidays': {
                'labour': '05-01' ,
                'christmas-day': '12-25'
            }
        }
        extras_list = [
            { 'key': 'foo', 'value': 'bar' } ,
            { 'key': 'inners', 'value': '["mercury", "venus", "earth", "mars"]' } ,
            {'key': 'holidays', 'value': '{"christmas-day": "12-25", "labour": "05-01"}'}
        ]

        _assert_equal(extras_as_list(extras_dict), extras_list)

class TestPlugin(FisbrokerTestBase):

    def test_open_data_wfs_service(self):
        # Create source1
        wfs_fixture = {
            'title': 'Test Source',
            'name': 'test-source',
            'url': u'http://127.0.0.1:8999/wfs-open-data.xml',
            'object_id': u'65715c6e-bbaf-3def-982b-3b5156272da7',
            'source_type': u'fisbroker'
        }

        source, job = self._create_source_and_job(wfs_fixture)

        harvest_object = self._run_job_for_single_document(job, wfs_fixture['object_id'])

        package_dict = get_action('package_show_rest')(self.context,{'id':harvest_object.package_id})

        # Package was created
        assert package_dict
        _assert_equal(package_dict['state'], u'active')
        _assert_equal(harvest_object.current, True)

        # Package has correct tags (filtering was successful)
        expected_tags = [
            'Ausgangsmaterial',
            u'Basens\xe4ttigung',
            'Berlin',
            'Boden',
            'Bodenart',
            'Bodengesellschaft',
            u'B\xf6den',
            'KAKeff',
            u'N\xe4hrstoffversorgung',
            'Oberboden',
            'Sachdaten',
            'Umweltatlas',
            'Unterboden',
            'infoFeatureAccessService',
            'inspireidentifiziert',
            'pH-Wert',
        ]
        _assert_equal(package_dict['tags'], expected_tags)

        # Package has correct contact info
        _assert_equal(package_dict['author'], u"Senatsverwaltung f\xFCr Umwelt, Verkehr und Klimaschutz Berlin")
        _assert_equal(package_dict['maintainer_email'], "michael.thelemann@senuvk.berlin.de")
        _assert_equal(package_dict['maintainer'], "Hr. Dr. Thelemann")

        # Package has correct license and attribution
        _assert_equal(package_dict['license_id'], "dl-de-by-2.0")
        _assert_equal(package_dict['extras']['attribution_text'],
                      "Umweltatlas Berlin / [Titel des Datensatzes]")

        # Package has correct reference dates
        _assert_equal(package_dict['extras']['date_released'], "2018-08-13")
        _assert_equal(package_dict['extras']['date_updated'], "2018-08-13")

        # Package has correct number of resources (i.e., uniqing was successful)
        _assert_equal(len(package_dict['resources']), 4)

        # url
        _assert_equal(
            package_dict['url'], "https://fbinter.stadt-berlin.de/fb?loginkey=alphaDataStart&alphaDataId=s01_11_07naehr2015@senstadt")

        # preview graphic - check if description contains something that looks like one
        assert u"![Vorschaugrafik zu Datensatz 'Nährstoffversorgung des Oberbodens 2015 (Umweltatlas)'](https://fbinter.stadt-berlin.de/fb_daten/vorschau/sachdaten/svor_default.gif)" in package_dict['notes']

        # title
        _assert_equal(
            u"Nährstoffversorgung des Oberbodens 2015 (Umweltatlas) - [WFS]", package_dict['title'])

        # name
        _assert_equal(
            "nahrstoffversorgung-des-oberbodens-2015-umweltatlas-wfs-65715c6e", package_dict['name']
        )

    def test_empty_config(self):
        '''Test that an empty config just returns unchanged.'''
        _assert_equal(FisbrokerPlugin().validate_config(None), None)
        _assert_equal(FisbrokerPlugin().validate_config({}), {})

    def test_import_since_must_be_valid_iso(self):
        '''Test that the `import_since` config must be a valid ISO8601 date.'''
        config = '{ "import_since": "2019-01-01" }'
        assert FisbrokerPlugin().validate_config(config)
        # invalid date:
        config = '{ "import_since": "2019.01.01" }'
        with assert_raises(ValueError):
            assert FisbrokerPlugin().validate_config(config)

    def test_timeout_must_be_int(self):
        '''Test that the `timeout` config must be an int.'''
        config = '{ "timeout": 30 }'
        assert FisbrokerPlugin().validate_config(config)
        # invalid timout:
        config = '{ "timeout": "hurtz" }'
        with assert_raises(ValueError):
            assert FisbrokerPlugin().validate_config(config)

    def test_timedelta_must_be_int(self):
        '''Test that the `timedelta` config must be an int.'''
        config = '{ "timedelta": 2 }'
        assert FisbrokerPlugin().validate_config(config)
        # invalid timedelta:
        config = '{ "timedelta": "two" }'
        with assert_raises(ValueError):
            assert FisbrokerPlugin().validate_config(config)
