import os
import shutil
import tempfile
import unittest

os.environ.setdefault("BMVC_PBKDF2_ITER", "1000")  # hash rápido nos testes


class TempDBCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
