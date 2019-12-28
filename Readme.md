# fs.minizip

fs.minizip is a project to wrap [pyminizip] for python [filesystem].

The original python filesystem project does not deal with password protected
zip file since current Python does not support.
This project integrates *pyminizip* to *fs* and thus we could create/write zip
file with password.

[pyminizip]: https://github.com/smihica/pyminizip
[filesystem]: https://github.com/PyFilesystem/pyfilesystem2


## Limitation

*pyminizip* does not provide detailed API to specific file info, and thus many
of the function from *fs* is ignored (e.g. file modified time).

Also, this project is based on [pyfilesystem2#361] which introduced `password`
argument to `ZipFS`. Since the based commits is not merged, users might install
from branch [before-merge].

[pyfilesystem2#361]: https://github.com/PyFilesystem/pyfilesystem2/pull/361
[before-merge]: https://github.com/tzing/fs_minizip/tree/before-merge


## Install

Would provides pip install link after stable.

For the current version, use [poetry]:

```bash
poetry add git+https://github.com/tzing/fs_minizip.git
```

[poetry]: https://github.com/python-poetry/poetry


## Usage

simply import this project, and use the native method to call `ZipFS`:

```python
import fs
import fs_minizip

zip_ = fs.open_fs("zip://foobar.zip")
# or
zip_ = fs.zipfs.ZipFS("zip://foobar.zip", write=True, password=b'1234')
```

this project would replace `ZipFS` to the one that supports password when you
import it.
