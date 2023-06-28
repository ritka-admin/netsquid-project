from netsquid.components import (
    Port,
    QSource,
    INSTR_X, INSTR_Z
)
from netsquid.nodes import node
from netsquid.protocols.nodeprotocols import NodeProtocol


def perform_correction(endnode, cur_state):
    if cur_state == 1:
        # |01>
        endnode.qmemory.execute_instruction(INSTR_X)
    elif cur_state == 2:
        # |11>
        endnode.qmemory.execute_instruction(INSTR_Z)
        endnode.qmemory.execute_instruction(INSTR_X)
    elif cur_state == 3:
        # |10>
        endnode.qmemory.execute_instruction(INSTR_Z)


class EntangleNodes(NodeProtocol):
    _is_source: bool = False
    _is_repeater: bool = False
    _is_endnode: bool = False
    _qsource_name: node = None
    _qmem_input_ports: [Port] = []

    def __init__(self, on_node: node, name: str, is_source: bool = False, is_repeater: bool = False,
                 is_endnode: bool = False):
        """
        Parameters:
            on_node: Node to run this protocol on
            is_source: Whether the node serves as a source
            is_repeater: Whether the node serves as a repeater
            is_endnode: Whether the node serves as an endnode (receiver)
            name: Name of the protocol
        """
        super().__init__(node=on_node, name=name)

        self._is_source = is_source
        self._is_repeater = is_repeater
        self._is_endnode = is_endnode

        if not self._is_source:
            self._qmem_input_ports.append(self.node.qmemory.ports["qin0"])
            self.node.qmemory.mem_positions[0].in_use = True

        if self._is_repeater:
            self._qmem_input_ports.append(self.node.qmemory.ports["qin1"])
            self.node.qmemory.mem_positions[1].in_use = True

    def run(self) -> None:
        """
        Send entangled qubits of the source to the two destination nodes.
        """
        if self._is_source or self._is_endnode:
            self.node.subcomponents[self._qsource_name].trigger()

        if not self._is_source:
            yield self.await_port_input(self._qmem_input_ports[0])

        if self._is_endnode:
            yield self.await_port_input(self._qmem_input_ports[1])

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
