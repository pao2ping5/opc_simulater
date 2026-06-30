"""
Compatibility shim: provides the ``opcua`` module interface as a lightweight
in-process mock.  ``asyncua`` 2.x is fully async and cannot be wrapped
synchronously without heavy refactoring.  This mock provides enough of the
``opcua.Server`` / ``opcua.ua`` surface to let the web console start so we
can focus on the UI experience.

Real OPC UA wire protocol is not needed for the Web Console demonstration.
"""

from __future__ import annotations

import enum
from typing import Any, Dict, List, Tuple


# ── ua helpers ──────────────────────────────────────────────────────────────


class VariantType(enum.IntEnum):
    Null = 0
    Boolean = 1
    SByte = 2
    Byte = 3
    Int16 = 4
    UInt16 = 5
    Int32 = 6
    UInt32 = 7
    Int64 = 8
    UInt64 = 9
    Float = 10
    Double = 11
    String = 12
    DateTime = 13
    Guid = 14
    ByteString = 15
    XmlElement = 16
    NodeId = 17
    ExpandedNodeId = 18
    StatusCode = 19
    QualifiedName = 20
    LocalizedText = 21
    ExtensionObject = 22
    DataValue = 23
    Variant = 24
    DiagnosticInfo = 25


class NodeIdType(enum.IntEnum):
    TwoByte = 0
    FourByte = 1
    Numeric = 2
    String = 3
    Guid = 4
    Opaque = 5


class NodeId:
    def __init__(
        self,
        identifier: Any = 0,
        namespaceidx: int = 0,
        nodeidtype: NodeIdType = NodeIdType.Numeric,
    ) -> None:
        self.Identifier = identifier
        self.NamespaceIndex = namespaceidx
        self.NodeIdType = nodeidtype

    def __repr__(self) -> str:
        return (
            f"NumericNodeId(Identifier={self.Identifier!r}, "
            f"NamespaceIndex={self.NamespaceIndex!r}, "
            f"NodeIdType=<NodeIdType.{self.NodeIdType.name}: "
            f"{self.NodeIdType.value}>)"
        )


class _ObjectsStub:
    """A stand-in for the OPC UA Objects node — we just need add_folder."""

    def __init__(self, server: "Server") -> None:
        self._server = server
        self._children: Dict[str, "_FolderStub"] = {}

    def add_folder(self, nodeid: NodeId, name: str) -> "_FolderStub":
        ident = str(nodeid.Identifier) if isinstance(nodeid, NodeId) else str(nodeid)
        folder = _FolderStub(self._server, name)
        self._children[ident] = folder
        return folder


class _FolderStub:
    def __init__(self, server: "Server", name: str) -> None:
        self._server = server
        self.name = name
        self._children: Dict[str, "_FolderStub"] = {}
        self._variables: Dict[str, "_VariableStub"] = {}

    def add_folder(self, nodeid: Any, name: str) -> "_FolderStub":
        ident = str(nodeid.Identifier) if isinstance(nodeid, NodeId) else str(nodeid)
        folder = _FolderStub(self._server, name)
        self._children[ident] = folder
        return folder

    def add_variable(
        self, nodeid: Any, name: str, val: Any, varianttype: Any = None
    ) -> "_VariableStub":
        ident = str(nodeid.Identifier) if isinstance(nodeid, NodeId) else str(nodeid)
        var = _VariableStub(val)
        self._variables[ident] = var
        return var


class _VariableStub:
    def __init__(self, value: Any) -> None:
        self._value = value

    def write_value(self, val: Any) -> None:
        self._value = val

    def read_value(self) -> Any:
        return self._value

    def set_writable(self, writable: bool = True) -> None:
        pass

    def set_value(self, val: Any) -> None:
        self._value = val


# ── Server ──────────────────────────────────────────────────────────────────


class Server:
    """Mock OPC UA Server — just enough to not crash."""

    def __init__(self) -> None:
        self._endpoint = ""
        self._name = ""
        self._ns_idx = 0
        self.nodes = _ObjectsStub(self)

    def set_endpoint(self, url: str) -> None:
        self._endpoint = url

    def set_server_name(self, name: str) -> None:
        self._name = name

    def register_namespace(self, uri: str) -> int:
        self._ns_idx += 1
        return self._ns_idx

    def get_objects_node(self) -> _ObjectsStub:
        return self.nodes

    def set_values(self, values: List[Tuple[Any, Any]]) -> None:
        """values = [(node_id, val), ...]"""
        pass  # no-op for mock

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass


# Re-export so ``from opcua import Server, ua`` and ``from opcua.ua import ...`` work
class ua:
    VariantType = VariantType
    NodeId = NodeId
    NodeIdType = NodeIdType

    # Commonly referenced OPC UA base node ids
    class ObjectIds:
        ObjectsFolder = NodeId(85, 0)
        RootFolder = NodeId(84, 0)
        BaseObjectType = NodeId(58, 0)
        BaseDataVariableType = NodeId(63, 0)
        FolderType = NodeId(61, 0)
        Organizes = NodeId(35, 0)
        HasComponent = NodeId(47, 0)
