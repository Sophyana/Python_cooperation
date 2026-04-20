import unittest
import sqroots
impoer sys


class TestSome(unittest.TestCase):
	def test_normal(self):
		self.assertEqual(sqroots.sqroots("1 2 1"), '-1.0')
		self.assertEqual(sqroots.sqroots("1 2 3"), '')
		self.assertEqual(sqroots.sqroots("3 7 3"), "-1.0 -2.0")


	s = socket.socket(socket.AF_INET, sokcket.SOCK_STREAM)

	def setUpClass(cls):
		cls.proc = multiprocessing.Process(target=sqroo.serve)
		cls.proc.start()
		time.sleep(1) 


