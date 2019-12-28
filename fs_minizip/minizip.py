import typing
import zipfile

import fs
import pyminizip

from fs.base import FS
from fs.copy import copy_dir_if_newer
from fs.errors import CreateFailed
from fs.wrapfs import WrapFS
from fs.path import join
from fs import zipfs
from fs.zipfs import ReadZipFS


if typing.TYPE_CHECKING:
    from typing import BinaryIO, Optional, Text, Union, Any

__all__ = ["ZipFS", "ReadZipFS", "WriteZipFS"]


def write_zip(
    src_fs,  # type: FS
    filename,  # type: Text
    compression=zipfile.ZIP_DEFLATED,  # type: int
    encoding="utf-8",  # type: Text
    password=None,  # type: Optional[bytes]
):
    # type: (...) -> None
    """Write the contents of a filesystem to a zip file.

    Arguments:
        src_fs (~fs.base.FS): The source filesystem to compress.
        filename (str): Destination file, should be a file name.
        compression (int): Compression to use (one of the constants
            defined in the `zipfile` module in the stdlib). Defaults
            to `zipfile.ZIP_DEFLATED`.
        encoding (str):
             The encoding to use for filenames. The default is ``"utf-8"``,
             use ``"CP437"`` if compatibility with WinZip is desired.
        password (bytes):
            Password to protect the zip file.

    """
    if not isinstance(filename, str):
        raise TypeError("expect str for filename, got " + type(filename).__name__)
    if password is not None:
        zipfs._password_type_check(password)

    # extract existed file
    try:
        with zipfs.ReadZipFS(filename, encoding, password) as zip_:
            copy_dir_if_newer(zip_, "/", src_fs, "/")
    except CreateFailed:
        pass

    # collect files
    src_files = []
    dest_prefixes = []
    for prefix, _, files in src_fs.walk():
        for info in files:
            dst_name = join(prefix, info.name)
            src_files.append(src_fs.getsyspath(dst_name))
            dest_prefixes.append(prefix if prefix else "")

    # make zip
    if src_files:
        pyminizip.compress_multiple(
            src_files, dest_prefixes, filename, password, compression
        )


class ZipFS(WrapFS):
    """Read and write zip files.

    There are two ways to open a ZipFS for the use cases of reading
    a zip file, and creating a new one.

    If you open the ZipFS with  ``write`` set to `False` (the default)
    then the filesystem will be a read only filesystem which maps to
    the files and directories within the zip file. Files are
    decompressed on the fly when you open them.

    Here's how you might extract and print a readme from a zip file::

        with ZipFS('foo.zip') as zip_fs:
            readme = zip_fs.readtext('readme.txt')

    If you open the ZipFS with ``write`` set to `True`, then the ZipFS
    will be a empty temporary filesystem. Any files / directories you
    create in the ZipFS will be written in to a zip file when the ZipFS
    is closed.

    Here's how you might write a new zip file containing a readme.txt
    file::

        with ZipFS('foo.zip', write=True) as new_zip:
            new_zip.writetext(
                'readme.txt',
                'This zip file was written by PyFilesystem'
            )


    Arguments:
        file (str or io.IOBase): An OS filename, or an open file object.
        write (bool): Set to `True` to write a new zip file, or `False`
            (default) to read an existing zip file.
        compression (int): Compression to use (one of the constants
            defined in the `zipfile` module in the stdlib).
        temp_fs (str): An FS URL for the temporary filesystem used to
            store data prior to zipping.
        password (bytes): Password for extracting file from zip file.

    """

    def __new__(  # type: ignore
        cls,
        file,  # type: Union[Text, BinaryIO]
        write=False,  # type: bool
        compression=zipfile.ZIP_DEFLATED,  # type: int
        encoding="utf-8",  # type: Text
        temp_fs="temp://__ziptemp__",  # type: Text
        password=None,  # type: Optional[bytes]
    ):
        # type: (...) -> FS
        # This magic returns a different class instance based on the
        # value of the ``write`` parameter.
        if write:
            return WriteZipFS(
                file,
                compression=compression,
                encoding=encoding,
                temp_fs=temp_fs,
                password=password,
            )
        else:
            return ReadZipFS(file, encoding=encoding, password=password)

    if typing.TYPE_CHECKING:

        def __init__(
            cls,
            file,  # type: Union[Text, BinaryIO]
            write=False,  # type: bool
            compression=zipfile.ZIP_DEFLATED,  # type: int
            encoding="utf-8",  # type: Text
            temp_fs="temp://__ziptemp__",  # type: Text
            password=None,  # type: Optional[bytes]
        ):
            # type: (...) -> None
            pass


class WriteZipFS(zipfs.WriteZipFS):
    """A writable zip file.
    """

    def __init__(
        self,
        file,  # type: Union[Text, BinaryIO]
        compression=zipfile.ZIP_DEFLATED,  # type: int
        encoding="utf-8",  # type: Text
        temp_fs="temp://__ziptemp__",  # type: Text
        password=None,  # type: Optional[bytes]
    ):
        if password is not None:
            zipfs._password_type_check(password)
        self._password = password
        super(WriteZipFS, self).__init__(
            file=file, compression=compression, encoding=encoding, temp_fs=temp_fs,
        )

    def __repr__(self):
        # type: () -> Text
        t = "WriteMiniZipFS({!r}, compression={!r}, encoding={!r}, temp_fs={!r})"
        return t.format(self._file, self.compression, self.encoding, self._temp_fs_url)

    def __str__(self):
        # type: () -> Text
        return "<minizipfs-write '{}'>".format(self._file)

    def write_zip(
        self,
        file=None,  # type: Union[Text, BinaryIO, None]
        compression=None,  # type: Optional[int]
        encoding=None,  # type: Optional[Text]
        password=None,  # type: Optional[bytes]
    ):
        # type: (...) -> None
        """Write zip to a file.

        Arguments:
            file (str or io.IOBase, optional): Destination file, may be
                a file name or an open file handle.
            compression (int, optional): Compression to use (one of the
                constants defined in the `zipfile` module in the stdlib).
            encoding (str, optional): The character encoding to use
                (default uses the encoding defined in
                `~WriteZipFS.__init__`).

        Note:
            This is called automatically when the ZipFS is closed.

        """
        if not self.isclosed():
            write_zip(
                self._temp_fs,
                file or self._file,
                compression=compression or self.compression,
                encoding=encoding or self.encoding,
                password=password or self._password,
            )


# hacky way to override the original ZipFS
zipfs.__dict__["ZipFS"] = ZipFS
