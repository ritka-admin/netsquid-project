import netsquid as ns
from netsquid.components import (
    QuantumChannel,
    QuantumMemory,
    QSource,
    ClassicalChannel
)
from netsquid.nodes.network import Network
from netsquid.nodes import Node, DirectConnection

# ( create(A~A) ; transmit(A~A to A~R)  ||
# create(B~B) ; transmit(B~B to B~R)  ) ; swap (A~R and B~R to AB).


def create_bell_pair(node: Node):
    q1, q2 = ns.qubits.create_qubits(2)
    ns.qubits.combine_qubits([q1, q2])
    node.qmemory.put([q1, q2])


def create_physical_network() -> Network:
    network = Network("Network with repeater")

    node_A = Node("A")
    node_B = Node("B")
    repeater = Node("Repeater")

    node_A.add_subcomponent(QSource(name="QSource_A", int_num_ports=2))
    node_B.add_subcomponent(QSource(name="QSource_B", int_num_ports=2))

    node_A.add_subcomponent(QuantumMemory(name="A_memory", num_positions=2, port_names=["outAqm"]))
    node_B.add_subcomponent(QuantumMemory(name="B_memory", num_positions=2, port_names=["outBqm"]))
    repeater.add_subcomponent(QuantumMemory(name="R_memory", num_positions=2, port_names=["inA", "inB"]))

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

    # TODO: channel backward?
    channelAtoR_quantum = QuantumChannel(name="AtoR_channel_quantum")
    channelBtoR_quantum = QuantumChannel(name="BtoR_channel_quantum")

    portA, portRA = network.add_connection(node_A, repeater, channel_to=channelAtoR_quantum, label="quantum")
    portB, portRB = network.add_connection(node_B, repeater, channel_to=channelBtoR_quantum, label="quantum")

    # link existing ports to the port of the supercomponent
    node_A.subcomponents["QSource_A"].ports["qout0"].forward_output(node_A.ports[portA])
    node_B.subcomponents["QSource_B"].ports["qout0"].forward_output(node_B.ports[portB])

    # link qsource input port to qmemory output port and vice versa
    # node_A.subcomponents["QSource_A"].ports["qout1"].connect(node_A.qmemory.ports["outAqm"])
    # node_B.subcomponents["QSource_B"].ports["qout1"].connect(node_B.qmemory.ports["outBqm"])

    repeater.ports[portRA].forward_input(repeater.qmemory.ports["inA"])
    repeater.ports[portRB].forward_input(repeater.qmemory.ports["inB"])

    return network


if __name__ == '__main__':
    network = create_physical_network()
    create_bell_pair(network.get_node("A"))     # TODO: parallel the processes?
    create_bell_pair(network.get_node("B"))     # TODO: qubit generation should occur within qsource

# print(a.qmemory.peek(1))

# rounds: creation of pairs, ";" -- next round

