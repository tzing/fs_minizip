import unittest
import tempfile
import os
import zipfile
import base64

import fs.zipfs

import fs_minizip.minizip as module


class TestWriteReadZipFS(unittest.TestCase):
    def setUp(self):
        fh, self._temp_path = tempfile.mkstemp()
        os.close(fh)
        zipfile.ZipFile(self._temp_path, "w")

    def tearDown(self):
        os.remove(self._temp_path)

    def test_write(self):
        self.assertIsInstance(
            fs.zipfs.ZipFS(self._temp_path, write=True), module.WriteZipFS,
        )

    def test_read(self):
        self.assertIsInstance(
            fs.zipfs.ZipFS(self._temp_path, write=False), fs.zipfs.ReadZipFS,
        )


class TestWriteZipFunc(unittest.TestCase):
    def test_password_type(self):
        with self.assertRaises(TypeError):
            module.write_zip(fs.open_fs("temp://"), "foo.zip", password="bar")

    def test_append_files(self):
        ZIP_FILE = (
            "UEsDBAoACQAAAEQpnE+oZTJ+EAAAAAQAAAADABwAZm9vVVQJAAOw4wZeseMGXnV4C"
            "wABBPUBAAAEFAAAACQkboy9fs6YvsqnWAxaacFQSwcIqGUyfhAAAAAEAAAAUEsDBA"
            "oACQAAAEYpnE/ps6IEEAAAAAQAAAADABwAYmFyVVQJAAO04wZeteMGXnV4CwABBPU"
            "BAAAEFAAAABEIKx8B06nMog63AnuXGUlQSwcI6bOiBBAAAAAEAAAAUEsBAh4DCgAJ"
            "AAAARCmcT6hlMn4QAAAABAAAAAMAGAAAAAAAAQAAAKSBAAAAAGZvb1VUBQADsOMGX"
            "nV4CwABBPUBAAAEFAAAAFBLAQIeAwoACQAAAEYpnE/ps6IEEAAAAAQAAAADABgAAA"
            "AAAAEAAACkgV0AAABiYXJVVAUAA7TjBl51eAsAAQT1AQAABBQAAABQSwUGAAAAAAI"
            "AAgCSAAAAugAAAAAA"
        )

        src = fs.open_fs("temp://")
        src.writetext("bar", "hello world")

        with tempfile.NamedTemporaryFile(suffix=".zip") as fp:
            fp.write(base64.b64decode(ZIP_FILE))
            fp.seek(0)

            module.write_zip(src, fp.name, password=b"1234")

            with zipfile.ZipFile(fp.name) as zip_:
                zip_.setpassword(b"1234")
                with zip_.open("foo", "r") as fp:
                    self.assertEqual(fp.read(), b"foo\n")
                with zip_.open("bar", "r") as fp:
                    self.assertEqual(fp.read(), b"hello world")

    def test_create_without_pass(self):
        src = fs.open_fs("temp://")
        src.makedir("foo")
        src.writetext("foo/bar", "foobar")
        src.writetext("bar", "bar")

        with tempfile.TemporaryDirectory() as tmpdir:
            fn = os.path.join(tmpdir, "tmp.zip")
            module.write_zip(src, fn)

            with zipfile.ZipFile(fn) as zip_:
                with zip_.open("foo/bar", "r") as fp:
                    self.assertEqual(fp.read(), b"foobar")
                with zip_.open("bar", "r") as fp:
                    self.assertEqual(fp.read(), b"bar")

    def test_create_with_pass(self):
        src = fs.open_fs("temp://")
        src.makedir("foo")
        src.writetext("foo/bar", "foobar")
        src.writetext("bar", "bar")

        with tempfile.TemporaryDirectory() as tmpdir:
            fn = os.path.join(tmpdir, "tmp.zip")
            module.write_zip(src, fn, password=b"1234")

            with zipfile.ZipFile(fn) as zip_:
                with self.assertRaises(RuntimeError):
                    zip_.extract("bar", fn)

                with zip_.open("bar", "r", pwd=b"1234") as fp:
                    self.assertEqual(fp.read(), b"bar")
