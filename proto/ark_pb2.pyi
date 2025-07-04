from typing import ClassVar, Iterable, Mapping, Optional, Text, Union

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper

DESCRIPTOR: _descriptor.FileDescriptor
GetStatus: ControlType
HealthCheck: ControlType
PullMetrics: ControlType
SetExpectedStatus: ControlType
SetMetrics: ControlType
SyncMultiLoRAs: ControlType

class BytesList(_message.Message):
    __slots__ = ["values"]
    VALUES_FIELD_NUMBER: ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[bytes]
    def __init__(self, values: Optional[Iterable[bytes]] = ...) -> None: ...

class ControlRequest(_message.Message):
    __slots__ = ["control_name", "control_type", "inputs", "req_id"]

    class InputsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: ClassVar[int]
        VALUE_FIELD_NUMBER: ClassVar[int]
        key: str
        value: Value
        def __init__(self, key: Optional[str] = ..., value: Optional[Union[Value, Mapping]] = ...) -> None: ...

    CONTROL_NAME_FIELD_NUMBER: ClassVar[int]
    CONTROL_TYPE_FIELD_NUMBER: ClassVar[int]
    INPUTS_FIELD_NUMBER: ClassVar[int]
    REQ_ID_FIELD_NUMBER: ClassVar[int]
    control_name: str
    control_type: ControlType
    inputs: _containers.MessageMap[str, Value]
    req_id: str
    def __init__(
        self,
        req_id: Optional[str] = ...,
        control_name: Optional[str] = ...,
        control_type: Optional[Union[ControlType, str]] = ...,
        inputs: Optional[Mapping[str, Value]] = ...,
    ) -> None: ...

class ControlResponse(_message.Message):
    __slots__ = ["control_name", "control_type", "outputs", "req_id"]

    class OutputsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: ClassVar[int]
        VALUE_FIELD_NUMBER: ClassVar[int]
        key: str
        value: Value
        def __init__(self, key: Optional[str] = ..., value: Optional[Union[Value, Mapping]] = ...) -> None: ...

    CONTROL_NAME_FIELD_NUMBER: ClassVar[int]
    CONTROL_TYPE_FIELD_NUMBER: ClassVar[int]
    OUTPUTS_FIELD_NUMBER: ClassVar[int]
    REQ_ID_FIELD_NUMBER: ClassVar[int]
    control_name: str
    control_type: ControlType
    outputs: _containers.MessageMap[str, Value]
    req_id: str
    def __init__(
        self,
        req_id: Optional[str] = ...,
        control_name: Optional[str] = ...,
        control_type: Optional[Union[ControlType, str]] = ...,
        outputs: Optional[Mapping[str, Value]] = ...,
    ) -> None: ...

class FloatList(_message.Message):
    __slots__ = ["values"]
    VALUES_FIELD_NUMBER: ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, values: Optional[Iterable[float]] = ...) -> None: ...

class InferenceRequest(_message.Message):
    __slots__ = ["inputs", "method", "model_name", "req_id"]

    class InputsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: ClassVar[int]
        VALUE_FIELD_NUMBER: ClassVar[int]
        key: str
        value: Value
        def __init__(self, key: Optional[str] = ..., value: Optional[Union[Value, Mapping]] = ...) -> None: ...

    INPUTS_FIELD_NUMBER: ClassVar[int]
    METHOD_FIELD_NUMBER: ClassVar[int]
    MODEL_NAME_FIELD_NUMBER: ClassVar[int]
    REQ_ID_FIELD_NUMBER: ClassVar[int]
    inputs: _containers.MessageMap[str, Value]
    method: str
    model_name: str
    req_id: str
    def __init__(
        self,
        req_id: Optional[str] = ...,
        model_name: Optional[str] = ...,
        inputs: Optional[Mapping[str, Value]] = ...,
        method: Optional[str] = ...,
    ) -> None: ...

class InferenceResponse(_message.Message):
    __slots__ = ["model_name", "outputs", "req_id"]

    class OutputsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: ClassVar[int]
        VALUE_FIELD_NUMBER: ClassVar[int]
        key: str
        value: Value
        def __init__(self, key: Optional[str] = ..., value: Optional[Union[Value, Mapping]] = ...) -> None: ...

    MODEL_NAME_FIELD_NUMBER: ClassVar[int]
    OUTPUTS_FIELD_NUMBER: ClassVar[int]
    REQ_ID_FIELD_NUMBER: ClassVar[int]
    model_name: str
    outputs: _containers.MessageMap[str, Value]
    req_id: str
    def __init__(
        self, req_id: Optional[str] = ..., model_name: Optional[str] = ..., outputs: Optional[Mapping[str, Value]] = ...
    ) -> None: ...

class Int64Dict(_message.Message):
    __slots__ = ["fields"]

    class FieldsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: ClassVar[int]
        VALUE_FIELD_NUMBER: ClassVar[int]
        key: int
        value: Value
        def __init__(self, key: Optional[int] = ..., value: Optional[Union[Value, Mapping]] = ...) -> None: ...

    FIELDS_FIELD_NUMBER: ClassVar[int]
    fields: _containers.MessageMap[int, Value]
    def __init__(self, fields: Optional[Mapping[int, Value]] = ...) -> None: ...

class Int64List(_message.Message):
    __slots__ = ["values"]
    VALUES_FIELD_NUMBER: ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, values: Optional[Iterable[int]] = ...) -> None: ...

class StringList(_message.Message):
    __slots__ = ["values"]
    VALUES_FIELD_NUMBER: ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, values: Optional[Iterable[str]] = ...) -> None: ...

class Struct(_message.Message):
    __slots__ = ["fields"]

    class FieldsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: ClassVar[int]
        VALUE_FIELD_NUMBER: ClassVar[int]
        key: str
        value: Value
        def __init__(self, key: Optional[str] = ..., value: Optional[Union[Value, Mapping]] = ...) -> None: ...

    FIELDS_FIELD_NUMBER: ClassVar[int]
    fields: _containers.MessageMap[str, Value]
    def __init__(self, fields: Optional[Mapping[str, Value]] = ...) -> None: ...

class Value(_message.Message):
    __slots__ = [
        "bool_",
        "bytes_",
        "bytes_list",
        "float_",
        "float_list",
        "int64_",
        "int64_dict",
        "int64_list",
        "string_",
        "string_list",
        "struct_",
        "value_list",
    ]
    BOOL__FIELD_NUMBER: ClassVar[int]
    BYTES_LIST_FIELD_NUMBER: ClassVar[int]
    BYTES__FIELD_NUMBER: ClassVar[int]
    FLOAT_LIST_FIELD_NUMBER: ClassVar[int]
    FLOAT__FIELD_NUMBER: ClassVar[int]
    INT64_DICT_FIELD_NUMBER: ClassVar[int]
    INT64_LIST_FIELD_NUMBER: ClassVar[int]
    INT64__FIELD_NUMBER: ClassVar[int]
    STRING_LIST_FIELD_NUMBER: ClassVar[int]
    STRING__FIELD_NUMBER: ClassVar[int]
    STRUCT__FIELD_NUMBER: ClassVar[int]
    VALUE_LIST_FIELD_NUMBER: ClassVar[int]
    bool_: bool
    bytes_: bytes
    bytes_list: BytesList
    float_: float
    float_list: FloatList
    int64_: int
    int64_dict: Int64Dict
    int64_list: Int64List
    string_: str
    string_list: StringList
    struct_: Struct
    value_list: ValueList
    def __init__(
        self,
        float_list: Optional[Union[FloatList, Mapping]] = ...,
        int64_list: Optional[Union[Int64List, Mapping]] = ...,
        bytes_list: Optional[Union[BytesList, Mapping]] = ...,
        float_: Optional[float] = ...,
        int64_: Optional[int] = ...,
        bytes_: Optional[bytes] = ...,
        string_list: Optional[Union[StringList, Mapping]] = ...,
        string_: Optional[str] = ...,
        struct_: Optional[Union[Struct, Mapping]] = ...,
        value_list: Optional[Union[ValueList, Mapping]] = ...,
        int64_dict: Optional[Union[Int64Dict, Mapping]] = ...,
        bool_: bool = ...,
    ) -> None: ...

class ValueList(_message.Message):
    __slots__ = ["values"]
    VALUES_FIELD_NUMBER: ClassVar[int]
    values: _containers.RepeatedCompositeFieldContainer[Value]
    def __init__(self, values: Optional[Iterable[Union[Value, Mapping]]] = ...) -> None: ...

class ControlType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []  # type: ignore
