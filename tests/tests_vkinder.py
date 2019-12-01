import unittest
import time
from pathlib import Path
import json
import tracemalloc
from tests.tests_service import display_top
from pymongo import MongoClient

from Vkinder import Vkinder

auth_dict = {}


class TestVkinder(unittest.TestCase):
    def setUp(self):
        current_path = str(Path.cwd()).strip('tests')
        p_auth = (current_path
                  + r'\fixtures\tests_vkinder_fixtures.json')
        with open(p_auth, 'r', encoding='utf-8') as auth:
            auth_dict.update(json.load(auth))
        self.u_login = auth_dict['u_login']
        self.u_password = auth_dict['u_password']

        self.test_user = Vkinder(self.u_login, self.u_password)
        time.sleep(10)

    def test_getting_subj_info(self):
        self.subj_info = self.test_user.get_subject_info()
        self.assertIn(self.subj_info['id'], self.subj_info.values())
        self.assertEqual(self.subj_info['id'], self.test_user.id)
        self.assertIn(self.subj_info['age'], self.subj_info.values())

    def test_making_search_req(self):
        self.make_search = self.test_user.make_search_request()
        self.assertTrue(self.make_search['count'])
        self.assertGreater(int(self.make_search['count']), 0)
        self.assertTrue(self.make_search['items'])
        self.assertGreater(len(self.make_search['items']), 0)

    def test_search_request_processing(self):
        self.search_process = (self.test_user.
                               search_request_processing())
        self.assertLessEqual(len(self.search_process), 10)

    def test_json_output(self):
        self.res_json = self.test_user.json_output()
        for item in self.res_json.keys():
            self.assertIn(self.res_json[f'{item}']['Photo01'],
                          self.res_json[f'{item}'].values())

            self.assertIn(self.res_json[f'{item}']['profile_link'],
                          self.res_json[f'{item}'].values())

    def test_finding_a_match(self):
        self.test_json = self.test_user.json_output()
        self.res_match = self.test_user.find_a_match(
            json_dict=self.test_json)
        self.json_file = self.test_user.file_name

        self.db_coll = self.test_user.db_coll_name
        self.assertTrue(self.db_coll.count_documents({}, limit=1))

        self.cursor = self.db_coll.find({'_id': self.res_match})
        self.assertTrue(self.cursor)

        self.cursor_list = list(self.db_coll.find({}))
        self.assertTrue(self.cursor_list)

        print('DB test passed')

        with open(self.json_file, 'rt',
                  encoding='utf8') as test_json:
            self.test_data = json.load(test_json)
            # print(self.test_data)
            for key in self.test_data.keys():
                self.assertIn(key, self.test_json.keys())

        print('File test passed')


def vkinder_test_suite():
    suite = unittest.TestSuite()
    suite.addTest(TestVkinder('test_getting_subj_info'))
    suite.addTest(TestVkinder('test_making_search_req'))
    suite.addTest(TestVkinder('test_search_request_processing'))
    suite.addTest(TestVkinder('test_json_output'))
    suite.addTest(TestVkinder('test_finding_a_match'))
    return suite


if __name__ == '__main__':
    tracemalloc.start()

    runner = unittest.TextTestRunner()
    runner.run(vkinder_test_suite())

    snapshot = tracemalloc.take_snapshot()
    display_top(snapshot)
