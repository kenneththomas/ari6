import sys
import unittest

sys.path.insert(0,'../')
sys.path.insert(0,'.')
import control as ct
import mememgr as mm

class admintests(unittest.TestCase):
    def test_admin_succeed(self):
        self.assertTrue(ct.admincheck('breezyexcursion#9570'))

    def test_admin(self):
        self.assertFalse(ct.admincheck('peter/chucky/zach'))


class bwmtests(unittest.TestCase):
    def test_netorare(self):
        # netorare is a banned word. payload should come back with delete=true
        payload = ct.bannedwordsmgr('netorare', 'bobby')
        self.assertTrue(payload.delete)

    def test_list(self):
        # add gris to the banned words list, and check bw list. gris should be there
        ct.bannedwords.append('gris')
        payload = ct.bannedwordsmgr('!bw list', 'bobby')
        self.assertTrue('gris' in payload.message)

class mememgr_tests(unittest.TestCase):
    def test_bad_name(self):
        badname = 'carmelo anthony#7'
        self.assertTrue(mm.cleanup_username(badname),'badname')

    def test_good_name(self):
        goodname = 'pete123'
        self.assertTrue(mm.cleanup_username(goodname),'pete123')