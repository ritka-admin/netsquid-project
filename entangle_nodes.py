from netsquid.protocols.nodeprotocols import NodeProtocol
from netsquid.nodes import node
from netsquid.components import Port, QSource
# from netsquid.protocols.serviceprotocol import Signals


class EntangleNodes(NodeProtocol):
    _is_source: bool = False
    _qsource_name: node = None
    _input_mem_position: int = 0
    _qmem_input_port: Port = None

    def __init__(self, on_node: node, is_source: bool, name: str, input_mem_pos: int = 1) -> None:
        """
        Constructor for the EntangleNode protocol class.
        :param on_node: Node to run this protocol on
        :param is_source: Whether this protocol should act as a source or a receiver. Both are needed
        :param name: Name of the protocol
        :param input_mem_pos: Index of quantum memory position to expect incoming qubits on. Default is 0
        """
        super().__init__(node=on_node, name=name)

        self._is_source = is_source

        if not self._is_source:
            self._input_mem_position = input_mem_pos
            self._qmem_input_port = self.node.qmemory.ports[f"qin{self._input_mem_position}"]
            self.node.qmemory.mem_positions[self._input_mem_position].in_use = True

    def run(self) -> None:
        """
        Send entangled qubits of the source and destination nodes.
        """
        if self._is_source:
            self.node.subcomponents[self._qsource_name].trigger()
        else:
            yield self.await_port_input(self._qmem_input_port)
            # self.send_signal(Signals.SUCCESS, self._input_mem_position)

    @property
    def is_connected(self) -> bool:
        if self._is_source:
            for name, subcomp in self.node.subcomponents.items():
                if isinstance(subcomp, QSource):
                    self._qsource_name = name
                    break
            else:
                return False

        return True
