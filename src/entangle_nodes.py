from netsquid.components import (
    QuantumChannel,
    QuantumProcessor,
    QSource,
    ClassicalChannel,
    SourceStatus,
    Port
)
from netsquid.protocols.nodeprotocols import NodeProtocol
from netsquid.nodes import node
from netsquid.nodes.network import Network, Node, DirectConnection
# from netsquid.protocols.serviceprotocol import Signals
from netsquid.qubits import StateSampler
from src.states import *


def create_physical_network() -> Network:
    network = Network("Network with repeater")

    node_A = Node("A")
    node_B = Node("B")
    repeater = Node("Repeater")

    node_A.add_subcomponent(QSource(name="QSource_A", state_sampler=StateSampler([b00]),
                                    status=SourceStatus.EXTERNAL, num_ports=2))
    node_B.add_subcomponent(QSource(name="QSource_B", state_sampler=StateSampler([b00]),
                                    status=SourceStatus.EXTERNAL, num_ports=2))

    # ports for qmemory communication
    node_A.subcomponents["QSource_A"].add_ports(["qout1"])
    node_B.subcomponents["QSource_B"].add_ports(["qout1"])

    node_A.add_subcomponent(QuantumProcessor(name="A_memory", num_positions=2, fallback_to_nonphysical=True))
    node_B.add_subcomponent(QuantumProcessor(name="B_memory", num_positions=2, fallback_to_nonphysical=True))
    repeater.add_subcomponent(QuantumProcessor(name="R_memory", num_positions=2, fallback_to_nonphysical=True))

    network.add_nodes([node_A, node_B, repeater])

    channelAtoR_classical = ClassicalChannel(name="AtoR_channel_classical")
    channelRtoA_classical = ClassicalChannel(name="RtoA_channel_classical")

    channelBtoR_classical = ClassicalChannel(name="BtoR_channel_classical")
    channelRtoB_classical = ClassicalChannel(name="RtoB_channel_classical")

    connectionA_R_classical = DirectConnection(name="AtoR_connection_c", channel_AtoB=channelAtoR_classical,
                                     channel_BtoA=channelRtoA_classical)
    connectionB_R_classical = DirectConnection(name="BtoR_connection_c", channel_AtoB=channelBtoR_classical,
                                     channel_BtoA=channelRtoB_classical)

    network.add_connection(node_A, repeater, connection=connectionA_R_classical)
    network.add_connection(node_B, repeater, connection=connectionB_R_classical)

    channelAtoR_quantum = QuantumChannel(name="AtoR_channel_quantum")
    channelBtoR_quantum = QuantumChannel(name="BtoR_channel_quantum")

    portA, portRA = network.add_connection(node_A, repeater, channel_to=channelAtoR_quantum, label="quantum")
    portB, portRB = network.add_connection(node_B, repeater, channel_to=channelBtoR_quantum, label="quantum")

    # link existing ports to the port of the supercomponent
    node_A.subcomponents["QSource_A"].ports["qout0"].forward_output(node_A.ports[portA])
    node_B.subcomponents["QSource_B"].ports["qout0"].forward_output(node_B.ports[portB])

    # link qsource input port to qmemory output port and vice versa
    node_A.subcomponents["QSource_A"].ports["qout1"].connect(node_A.qmemory.ports["qin0"])
    node_B.subcomponents["QSource_B"].ports["qout1"].connect(node_B.qmemory.ports["qin0"])

    repeater.ports[portRA].forward_input(repeater.qmemory.ports["qin0"])
    repeater.ports[portRB].forward_input(repeater.qmemory.ports["qin1"])
    return network


class EntangleNodes(NodeProtocol):
    _is_source: bool = False
    _qsource_name: node = None
    _input_mem_position: int = 0
    _qmem_input_port: Port = None

    def __init__(self, on_node: node, is_source: bool, name: str, input_mem_pos: int = 0) -> None:
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
