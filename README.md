# Documember

A Python application to scan a given module for undocumented members.

## Usage

With Python 3.11+ and Git, you can install this application with:

```py
pip install git+https://github.com/thegamecracks/documember@v0.1.4
```

Then invoke the CLI using `documember` or `python -m documember`.

## Examples

Showing public members in a module:

```ruby
$ pip install git+https://github.com/thegamecracks/asyreader
$ documember asyreader
asyreader (undocumented)
  reader (undocumented)
    AsyncReader
      close()
      read()
      start()
    Readable (inherited)
      close() (undocumented)
      read() (undocumented)
  AsyncReader
    close()
    read()
    start()
  Readable (inherited)
    close() (undocumented)
    read() (undocumented)
```

Showing public and private members:

```ruby
$ documember asyreader --include-private
asyreader (undocumented)
  reader (undocumented)
    AsyncReader
      ._read_queue
      ._thread
      ._file
      ._start_fut
      ._is_closing
      ._close_fut
      _cancel_queue() (undocumented)
      _open_file() (undocumented)
      ...
```

Showing dunder/magic methods:

```ruby
$ documember asyreader --include-dunder
asyreader (undocumented)
  reader (undocumented)
    AsyncReader
      __aenter__() (undocumented)
      __aexit__() (undocumented)
      __init__() (inherited)
      close()
      ...
```

Showing docstrings for members that are documented:

```ruby
$ documember asyreader --show-docstrings
asyreader (undocumented)
  reader (undocumented)
    AsyncReader
      close()
        Close the current file and wait for the reader to stop.
      read()
        Request the file to be read by the reader thread.
      ...

$ documember asyreader --show-full-docstrings
asyreader (undocumented)
  reader (undocumented)
    AsyncReader
      close()
        Close the current file and wait for the reader to stop.

        If a function was given to open the file, any exceptions raised
        by it will be propagated here.

        This method is idempotent.
      ...
```

Showing imported members:

```ruby
$ documember asyreader --include-imported
asyreader (undocumented)
  reader (undocumented)
    AsyncReader
      close()
      read()
      start()
    Readable (inherited)
      close() (undocumented)
      read() (undocumented)
    typing.Any
    typing.Generic
    typing.ParamSpec
    typing.Protocol
    ...
```

Showing members in a module that defines [`__all__`](https://docs.python.org/3/tutorial/modules.html#importing-from-a-package):

```ruby
# In this case,
# __all__ = ("ModuleSummary", "parse_module", "format_module_summary")
$ documember documember
documember (__all__)
  ModuleSummary
    .name
    .qualname
    .all
    .doc
    .submodules
    .classes
    .functions
  format_module_summary
  parse_module

$ documember documember --ignore-all
documember (__all__)
  DocstringDetail (undocumented)
    FULL
    NONE
    ONE_LINE
  ModuleSummary
    ...
  format_module_summary
  main (undocumented)
  parse_module
```

## License

This project can be used under the MIT License.
