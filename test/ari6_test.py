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
        payload = ct.controlmgr('netorare', 'bobby')
        self.assertTrue(payload.delete)

    def test_periodt(self):
        # periodt is a banned word. payload should come back with delete=true
        payload = ct.controlmgr('periodt', 'bobby')
        self.assertTrue(payload.delete)

    def test_list(self):
        # add gris to the banned words list, and check bw list. gris should be there
        ct.bannedwords.append('gris')
        payload = ct.controlmgr('!bw list', 'bobby')
        self.assertTrue('gris' in payload.message)

    def test_admincontrol_bwm_release(self):
        ct.controlmgr('!bw add pickle','bobby')
        p1 = ct.controlmgr('pickle','bobby')
        ct.controlmgr('!admin add bobby','breezyexcursion#9570')
        p2 = ct.controlmgr('!bw add pickle','bobby')
        p3 = ct.controlmgr('pickle','armando')
        p4 = ct.controlmgr('!release','bobby')

        result = False
        #satisfy all conditions for testcase to pass
        if not p1.delete:
            if p3.delete:
                if 'armando' in p4.message:
                    result = True

        self.assertTrue(result)

class mememgr_tests(unittest.TestCase):
    def test_bad_name(self):
        badname = 'carmelo anthony#7'
        self.assertEqual(mm.cleanup_username(badname),'badname')

    def test_good_name(self):
        goodname = 'pete123'
        self.assertEqual(mm.cleanup_username(goodname),'pete123')

    def test_repeat4x(self):
        repeatresults = []
        for i in range(0,4):
            repeatresults.append(mm.memes('pete my meat'))
        print(repeatresults)
        self.assertEqual(repeatresults[3][0],'pete my meat')

class sentience_tests(unittest.TestCase):
    def test_battlerap_cleanup(self):
        cleaned = mm.battlerap_cleanup('FATHER FIGURE BODYBUILDER\\')
        print(cleaned)
        self.assertFalse(cleaned.endswith('\\'))

if __name__ == '__main__':
    unittest.main()