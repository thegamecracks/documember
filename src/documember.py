"""Import a given module and scan its members.

By default, documember will take into consideration a module's __all__ variable
if defined, limiting what members will be checked. This takes precedent over
other options like --include-imported and --include-private. If you want to
bypass this restriction, you should use the --ignore-all option.

"""
from __future__ import annotations

import argparse
import enum
import importlib
import inspect
import logging
import sys
import types
from dataclasses import dataclass, field
from typing import Callable, Collection, Iterator, Type, cast

__all__ = ("ModuleSummary", "parse_module", "format_module_summary")

_INDENT = "  "

_log = logging.getLogger(__name__)


@dataclass
class ModuleSummary:
    # NOTE: @dataclass implicitly generates a docstring so this counts as documented
    name: str
    qualname: str
    all: list[str] | None
    doc: str
    submodules: list[ModuleSummary] = field(default_factory=list)
    classes: list[Type] = field(default_factory=list)
    functions: list[types.FunctionType] = field(default_factory=list)


def parse_module(
    module: types.ModuleType,
    *,
    ignore_all: bool = False,
) -> ModuleSummary:
    """Parse a module to produce a summary.

    :param module: The module to summarize.
    :param ignore_all:
        If True and the module defines __all__, only those members will
        be returned in the summary.

    """
    # TODO: I would rather have ignore_all be handled during formatting,
    #       but doing it here is convenient
    name = module.__name__.split(".")[-1]
    qualname = module.__name__

    all_: list[str] | None = None
    if hasattr(module, "__all__"):
        all_ = list(module.__all__)

    doc = inspect.getdoc(module) or ""
    parsed = ModuleSummary(name=name, qualname=qualname, all=all_, doc=doc)

    members = _get_module_members(
        module,
        all_=None if ignore_all else all_,
    )
    for name, value in members.items():
        if getattr(value, "__package__", "").startswith(module.__name__):
            value = cast(types.ModuleType, value)
            _log.info("Discovered submodule %s", value.__name__)
            submodule = parse_module(
                value,
                ignore_all=ignore_all,
            )
            parsed.submodules.append(submodule)
        elif inspect.isclass(value):
            _log.info("Discovered class %s", name)
            parsed.classes.append(value)
        elif inspect.isfunction(value):
            _log.info("Discovered function %s", name)
            parsed.functions.append(value)
    return parsed


def _get_module_members(
    module: types.ModuleType,
    *,
    all_: Collection[str] | None,
) -> dict[str, object]:
    def by_type(name: str) -> tuple[bool, str]:
        # Order by modules first, then non-modules
        # (yes, this sorting key is a bit confusing)
        value = getattr(module, name)
        return not inspect.ismodule(value), name

    names = vars(module).keys()
    if all_ is not None:
        names = names & set(all_)
    names = sorted(names, key=by_type)

    return {name: getattr(module, name) for name in names}


class DocstringDetail(enum.Enum):
    NONE = enum.auto()
    ONE_LINE = enum.auto()
    FULL = enum.auto()


def format_module_summary(
    module: ModuleSummary,
    *,
    docstring_detail: DocstringDetail,
    include_imported: bool,
    name_check: Callable[[str], bool],
) -> Iterator[str]:
    """Format a module summary into an iterator of lines.

    :param module: The module summary to format.
    :param docstring_detail:
        Defines the amount of detail to be shown for docstrings.
    :param name_check:
        A callable that can be used to filter out submodules,
        classes, methods within classes, and top-level functions
        by their name.

    """
    _log.info("Formatting module %s", module.qualname)
    yield module.name + _all_status(module) + _documented_status(module)

    for line in _docstring_snippet(module.doc, docstring_detail):
        yield _INDENT + line

    for line in _format_module_members(
        module,
        docstring_detail=docstring_detail,
        include_imported=include_imported,
        name_check=name_check,
    ):
        yield _INDENT + line


def _all_status(module: ModuleSummary) -> str:
    return "" if module.all is None else " (__all__)"


def _documented_status(x: object) -> str:
    return "" if _is_documented(x) else " (undocumented)"


def _is_documented(x: object) -> bool:
    if isinstance(x, ModuleSummary):
        doc = x.doc
    else:
        doc = getattr(x, "__doc__", "")
    return doc is not None and doc != ""


def _docstring_snippet(doc: object, detail: DocstringDetail) -> Iterator[str]:
    if detail == DocstringDetail.NONE:
        return

    # For convenience, allow passing non-docstrings and automatically extract
    if not isinstance(doc, (str, type(None))):
        doc = inspect.getdoc(doc)

    if doc is None or doc == "":
        return

    lines = doc.splitlines()
    if detail == DocstringDetail.ONE_LINE:
        yield lines[0]
    elif detail == DocstringDetail.FULL:
        yield from lines


def _format_module_members(
    module: ModuleSummary,
    *,
    docstring_detail: DocstringDetail,
    include_imported: bool,
    name_check: Callable[[str], bool],
) -> Iterator[str]:
    for submodule in module.submodules:
        if not name_check(submodule.name):
            _log.debug("Ignoring submodule %s", submodule.qualname)
            continue

        yield from format_module_summary(
            submodule,
            docstring_detail=docstring_detail,
            include_imported=include_imported,
            name_check=name_check,
        )

    def by_class_location(cls: Type) -> tuple[bool, bool, str]:
        # Order by classes in the same module first, then classes outside the module
        # (yes, this sorting key is a bit confusing)
        cls_module = inspect.getmodule(cls)
        return (
            cls_module is None,
            not getattr(cls_module, "__name__", "").startswith(module.qualname),
            cls.__name__,
        )

    for cls in sorted(module.classes, key=by_class_location):
        if not name_check(cls.__name__):
            _log.debug("Ignoring class %s.%s", module.qualname, cls.__name__)
            continue

        module_name = getattr(inspect.getmodule(cls), "__name__", "")
        if not module_name.startswith(module.qualname) and not include_imported:
            _log.debug("Ignoring class %s.%s", module_name, cls.__name__)
            _log.debug("%s, %s, %s", module_name, module.qualname, include_imported)
            continue

        yield from _format_class_summary(
            module,
            cls,
            docstring_detail=docstring_detail,
            name_check=name_check,
        )

    for func in module.functions:
        if not name_check(func.__name__):
            _log.debug("Ignoring function %s.%s", module.qualname, func.__name__)
            continue

        module_name = getattr(inspect.getmodule(func), "__name__", "")
        if module_name.startswith(module.qualname):
            _log.info("Formatting function %s.%s", module.qualname, func.__name__)
            yield func.__name__ + _documented_status(func)
            yield from _docstring_snippet(func, docstring_detail)
        elif include_imported:
            _log.info("Formatting function %s.%s", module_name, func.__name__)
            yield f"{module_name}.{func.__name__}"
        else:
            _log.debug("Ignoring function %s.%s", module_name, func.__name__)


def _format_class_summary(
    module: ModuleSummary,
    cls: Type,
    *,
    docstring_detail: DocstringDetail,
    name_check: Callable[[str], bool],
) -> Iterator[str]:
    cls_module = inspect.getmodule(cls)
    if cls_module is None:
        _log.debug("No module found for class %s", cls.__name__)
        yield cls.__name__
        return

    if not cls_module.__name__.startswith(module.qualname):
        _log.debug("Ignoring %s.%s", cls_module.__name__, cls.__name__)
        yield f"{cls_module.__name__}.{cls.__name__}"
        return

    _log.info("Formatting class %s.%s", module.qualname, cls.__name__)
    yield cls.__name__ + _documented_status(cls)
    for line in _format_class_members(
        cls,
        docstring_detail=docstring_detail,
        name_check=name_check,
    ):
        yield _INDENT + line


def _format_class_members(
    cls: Type,
    *,
    docstring_detail: DocstringDetail,
    name_check: Callable[[str], bool],
) -> Iterator[str]:
    def by_type(item):
        name, value = item
        return not inspect.isfunction(value), name

    for name, _ in getattr(cls, "__annotations__", {}).items():
        if not name_check(name):
            _log.debug("Ignoring annotation %s.%s", cls.__name__, name)
            continue

        yield "." + name

    for name, value in sorted(vars(cls).items(), key=by_type):
        if not name_check(name):
            _log.debug("Ignoring %s.%s", cls.__name__, name)
            continue
        elif inspect.isfunction(value):
            _log.info("Formatting method %s.%s", cls.__name__, name)
            yield name + "()" + _documented_status(value)
            for line in _docstring_snippet(value, docstring_detail):
                yield _INDENT + line
        else:
            _log.info("Formatting class attribute %s.%s", cls.__name__, name)
            yield name


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "module",
        help="The module to scan",
        type=importlib.import_module,
    )
    parser.add_argument(
        "--include-dunder",
        action="store_true",
        help="Include members with __double__ underscores",
    )
    parser.add_argument(
        "--include-imported",
        action="store_true",
        help="Include imported members",
    )
    parser.add_argument(
        "--include-private",
        action="store_true",
        help="Include members prefixed with _",
    )
    parser.add_argument(
        "--ignore-all",
        action="store_true",
        help="Do not limit module members to those defined in __all__",
    )
    docstring = parser.add_mutually_exclusive_group()
    docstring.set_defaults(docstring_detail=DocstringDetail.NONE)
    docstring.add_argument(
        "--show-docstrings",
        action="store_const",
        const=DocstringDetail.ONE_LINE,
        dest="docstring_detail",
        help="Show the first line of each member's docstring",
    )
    docstring.add_argument(
        "--show-full-docstrings",
        action="store_const",
        const=DocstringDetail.FULL,
        dest="docstring_detail",
        help="Show each member's entire docstring",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase logging verbosity",
    )

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(2)

    args = parser.parse_args()

    _setup_logging(args.verbose)

    module = parse_module(
        args.module,
        ignore_all=args.ignore_all,
    )

    def name_check(s: str) -> bool:
        if not args.include_dunder and _is_dunder(s):
            return False
        if not args.include_private and _is_private(s):
            return False
        return True

    summary = format_module_summary(
        module,
        docstring_detail=args.docstring_detail,
        include_imported=args.include_imported,
        name_check=name_check,
    )
    print("\n".join(summary))


def _setup_logging(verbose: int):
    if verbose == 0:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("L%(lineno)03d %(levelname)s: %(message)s"))
    _log.addHandler(handler)

    if verbose == 1:
        _log.setLevel(logging.INFO)
    else:
        _log.setLevel(logging.DEBUG)


def _is_dunder(s: str) -> bool:
    return s.startswith("__") and s.endswith("__")


def _is_private(s: str) -> bool:
    return s.startswith("_") and not _is_dunder(s)


if __name__ == "__main__":
    main()
