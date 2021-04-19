import unittest
import responses
from src.exceptions import NoAccessGroupError, NoUserProfileError
from src.search1_conversion import convert_result
from src.utils.config import config
from tests.unit.mocks.mocked import \
    get_data, \
    workspace_call, user_profile_call


# TODO test post processing
# TODO test the following fields: object_name, obj_id, version, type, creator


class Search1ConversionTest(unittest.TestCase):
    @responses.activate
    def test_search_objects_valid(self):
        responses.add_callback(responses.POST, config['workspace_url'],
                               callback=workspace_call)

        responses.add_callback(responses.POST, config['user_profile_url'],
                               callback=user_profile_call)

        # Using case-01 params, ES result and api result.
        _found, test_params = get_data(
            'SearchAPI/legacy/search_objects/case-01/params.json')
        _found, test_es_search_results = get_data(
            'elasticsearch/legacy/search_objects/case-01/result.json')
        _found, test_expected = get_data(
            'SearchAPI/legacy/search_objects/case-01/result.json')

        final = convert_result.search_objects(test_params, test_es_search_results,
                                              {'auth': None})

        # Remove unwanted comparisons.
        del final['search_time']
        del test_expected['search_time']

        self.maxDiff = None
        self.assertEqual(final, test_expected)

    @responses.activate
    def test_get_objects_valid(self):
        responses.add_callback(responses.POST, config['workspace_url'],
                               callback=workspace_call)

        responses.add_callback(responses.POST, config['user_profile_url'],
                               callback=user_profile_call)

        _found, test_params = get_data(
            'SearchAPI/legacy/get_objects/case-02/params.json')
        _found, test_es_search_results = get_data(
            'elasticsearch/legacy/get_objects/case-02/result.json')
        _found, test_expected = get_data(
            'SearchAPI/legacy/get_objects/case-02/result.json')

        final = convert_result.get_objects(test_params, test_es_search_results, {'auth': None})
        self.assertEqual(final, test_expected)

    def test_search_types_valid(self):
        _found, test_es_search_results = get_data(
            'elasticsearch/legacy/search_types/case-01/result.json')
        _found, test_expected = get_data(
            'SearchAPI/legacy/search_types/case-01/result.json')

        # Not that converting search_types does not require any
        # params or context.
        final = convert_result.search_types({}, test_es_search_results, {})

        self.assertEqual(final['type_to_count'], test_expected['type_to_count'])

    def test_fetch_narrative_info_no_hits(self):
        results = {
            'hits': []
        }
        ctx = {}
        result = convert_result._fetch_narrative_info(results, ctx)
        assert len(result) == 2
        assert result[0] == {}
        assert result[1] == {}

    # TODO: This condition should not occur in any object index!
    def test_fetch_narrative_info_no_access_group(self):
        results = {
            'hits': [{
                'doc': {}
            }]
        }
        with self.assertRaises(NoAccessGroupError):
            convert_result._fetch_narrative_info(results, {'auth': None})

    @responses.activate
    def test_fetch_narrative_info_owner_has_profile(self):
        responses.add_callback(responses.POST, config['workspace_url'],
                               callback=workspace_call)

        responses.add_callback(responses.POST, config['user_profile_url'],
                               callback=user_profile_call)

        _found, test_es_search_results = get_data(
            'elasticsearch/legacy/search_objects/case-01/result.json')
        _found, test_expected = get_data(
            'SearchAPI/legacy/search_objects/case-01/result.json')

        ctx = {
            'auth': None
        }
        result = convert_result._fetch_narrative_info(test_es_search_results, ctx)
        self.assertEqual(len(result), 2)

        expected_result = test_expected['access_group_narrative_info']
        self.assertEqual(result[1], expected_result)

    @responses.activate
    def test_fetch_narrative_info_owner_has_no_profile(self):
        responses.add_callback(responses.POST, config['workspace_url'],
                               callback=workspace_call)

        responses.add_callback(responses.POST, config['user_profile_url'],
                               callback=user_profile_call)
        results = {
            'hits': [{
                'doc': {
                    'access_group': 10056638
                }
            }]
        }
        meta = {
            'auth': None
        }
        with self.assertRaises(NoUserProfileError) as e:
            convert_result._fetch_narrative_info(results, meta)
        self.assertEqual(e.exception.message,
                         'A user profile could not be found for "kbaseuitestx"')

    def test_get_object_data_from_search_results(self):
        responses.add_callback(responses.POST, config['workspace_url'],
                               callback=workspace_call)
        responses.add_callback(responses.POST, config['user_profile_url'],
                               callback=user_profile_call)

        _found, test_params = get_data(
            'SearchAPI/legacy/search_objects/case-01/params.json')
        _found, test_es_search_results = get_data(
            'elasticsearch/legacy/search_objects/case-01/result.json')
        _found, test_expected = get_data(
            'SearchAPI/legacy/search_objects/case-01/result.json')

        post_processing = test_params['post_processing']
        converted = convert_result._get_object_data_from_search_results(
            test_es_search_results,
            post_processing)
        self.assertEqual(converted, test_expected['objects'])
