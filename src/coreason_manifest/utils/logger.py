# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import contextlib
import functools
from collections.abc import Callable, Generator
from typing import Any, ParamSpec, TypeVar

from loguru import logger

__all__ = ["bind_context", "logger", "trace", "trace_scope"]

P = ParamSpec("P")
R = TypeVar("R")


def bind_context(**kwargs: Any) -> Any:
    """Bind context to the logger for the current context.

    Returns a new logger instance with the bound context.
    """
    return logger.bind(**kwargs)


@contextlib.contextmanager
def trace_scope(name: str, **kwargs: Any) -> Generator[Any, None, None]:
    """Context manager to trace a scope of execution with structured context.

    Logs entry and exit (debug), and exceptions (error with stack trace).
    """
    context_logger = logger.bind(scope=name, **kwargs)
    context_logger.debug(f"Entering scope: {name}")
    try:
        yield context_logger
    except Exception as e:
        # 'exception' log level includes stack trace automatically
        context_logger.exception(f"Exception in scope: {name}")
        raise e
    else:
        context_logger.debug(f"Exiting scope: {name}")


def trace(name: str | None = None, **ctx_kwargs: Any) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to trace function execution."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        scope_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with trace_scope(scope_name, **ctx_kwargs):
                return func(*args, **kwargs)

        return wrapper

    return decorator
