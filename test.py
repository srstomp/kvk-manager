import unittest
import kvk

class Test(unittest.TestCase):
    def search_company_by_kvk(self):
        """
        Test if a company can be found by KVK number
        :return: JSON object with company details
        """
