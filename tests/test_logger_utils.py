# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from typing import Any
from loguru import logger

from coreason_manifest.utils.logger import bind_context, trace, trace_scope


def test_bind_context() -> None:
    # Helper to capture logs
    logs: list[Any] = []

    def sink(msg: Any) -> None:
        logs.append(msg.record)

    # We add a sink for this test
    handler_id = logger.add(sink, level="DEBUG")

    try:
        new_logger = bind_context(request_id="123")
        new_logger.info("Test message")

        assert len(logs) == 1
        assert logs[0]["extra"]["request_id"] == "123"
        assert logs[0]["message"] == "Test message"
    finally:
        logger.remove(handler_id)


def test_trace_scope_success() -> None:
    logs: list[Any] = []

    def sink(msg: Any) -> None:
        logs.append(msg.record)

    handler_id = logger.add(sink, level="DEBUG")

    try:
        with trace_scope("my_scope", user="alice"):
            logger.info("Inside scope (global)")

        entry = next(log for log in logs if "Entering scope: my_scope" in log["message"])
        assert entry["extra"]["scope"] == "my_scope"
        assert entry["extra"]["user"] == "alice"

        exit_log = next(log for log in logs if "Exiting scope: my_scope" in log["message"])
        assert exit_log["extra"]["scope"] == "my_scope"

    finally:
        logger.remove(handler_id)


def test_trace_scope_exception() -> None:
    logs: list[Any] = []

    def sink(msg: Any) -> None:
        logs.append(msg.record)

    handler_id = logger.add(sink, level="DEBUG")

    try:
        with (
            pytest.raises(ValueError, match="Something went wrong"),
            trace_scope("error_scope"),
        ):
            raise ValueError("Something went wrong")

        # Entry
        assert any("Entering scope: error_scope" in log["message"] for log in logs)

        # Exception
        err_log = next(log for log in logs if "Exception in scope: error_scope" in log["message"])
        assert err_log["level"].name == "ERROR"
        assert err_log["exception"] is not None
        # Verify stack trace is captured (loguru exception object is not empty)

    finally:
        logger.remove(handler_id)


def test_trace_decorator() -> None:
    logs: list[Any] = []

    def sink(msg: Any) -> None:
        logs.append(msg.record)

    handler_id = logger.add(sink, level="DEBUG")

    @trace(name="decorated_func", transaction="txn-1")
    def my_func(x: int) -> int:
        if x < 0:
            raise ValueError("Negative")
        return x * 2

    try:
        # Success case
        res = my_func(10)
        assert res == 20
        assert any("Entering scope: decorated_func" in log["message"] for log in logs)
        assert any("Exiting scope: decorated_func" in log["message"] for log in logs)

        logs.clear()

        # Failure case
        with pytest.raises(ValueError, match="Negative"):
            my_func(-1)

        assert any("Entering scope: decorated_func" in log["message"] for log in logs)
        assert any("Exception in scope: decorated_func" in log["message"] for log in logs)

        err_log = next(log for log in logs if "Exception in scope: decorated_func" in log["message"])
        assert err_log["extra"]["transaction"] == "txn-1"

    finally:
        logger.remove(handler_id)
