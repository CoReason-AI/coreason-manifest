# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from enum import StrEnum


class NodeType(StrEnum):
    AGENT = "agent"
    HUMAN = "human"
    SYSTEM = "system"
    SANDBOXED = "sandboxed"


class TopologyType(StrEnum):
    DAG = "dag"
    COUNCIL = "council"
    SWARM = "swarm"
    EVOLUTIONARY = "evolutionary"


class PatchOperation(StrEnum):
    ADD = "add"
    REMOVE = "remove"
    REPLACE = "replace"
    COPY = "copy"
    MOVE = "move"
    TEST = "test"


class InterventionTrigger(StrEnum):
    ON_START = "on_start"
    ON_NODE_TRANSITION = "on_node_transition"
    BEFORE_TOOL_EXECUTION = "before_tool_execution"
    ON_FAILURE = "on_failure"
    ON_CONSENSUS_REACHED = "on_consensus_reached"
    ON_MAX_LOOPS_REACHED = "on_max_loops_reached"


class SpanKind(StrEnum):
    CLIENT = "client"
    SERVER = "server"
    PRODUCER = "producer"
    CONSUMER = "consumer"
    INTERNAL = "internal"


class SpanStatusCode(StrEnum):
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


class DistributionType(StrEnum):
    GAUSSIAN = "gaussian"
    UNIFORM = "uniform"
    BETA = "beta"


class OptimizationDirection(StrEnum):
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


class CrossoverType(StrEnum):
    UNIFORM_BLEND = "uniform_blend"
    SINGLE_POINT = "single_point"
    HEURISTIC = "heuristic"


class MarkType(StrEnum):
    POINT = "point"
    LINE = "line"
    AREA = "area"
    BAR = "bar"
    RECT = "rect"
    ARC = "arc"


class ScaleType(StrEnum):
    LINEAR = "linear"
    LOG = "log"
    TIME = "time"
    ORDINAL = "ordinal"
    NOMINAL = "nominal"


class EncodingChannel(StrEnum):
    X = "x"
    Y = "y"
    COLOR = "color"
    SIZE = "size"
    OPACITY = "opacity"
    SHAPE = "shape"
    TEXT = "text"
