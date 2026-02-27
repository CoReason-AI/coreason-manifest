from enum import StrEnum


class NodeCapability(StrEnum):
    COMPUTER_USE = "computer_use"
    CODE_EXECUTION = "code_execution"
    WASM_EXECUTION = "wasm_execution"
