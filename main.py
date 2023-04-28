import numpy as np
import netsquid as ns
from netsquid.components import (
    QuantumChannel,
    QuantumMemory,
    QuantumProcessor,
    QSource,
    ClassicalChannel,
    SourceStatus
)
from netsquid.qubits import StateSampler
from netsquid.nodes.network import Network
from netsquid.nodes import Node, DirectConnection
from entangle_nodes import EntangleNodes
from netsquid import sim_run

# ( create(A~A) ; transmit(A~A to A~R)  ||
# create(B~B) ; transmit(B~B to B~R)  ) ; swap (A~R and B~R to AB).


s0 = np.array([[1], [0]], dtype=complex)  # |0>
s1 = np.array([[0], [1]], dtype=complex)  # |1>
s11 = np.kron(s1, s1)
s00 = np.kron(s0, s0)
b00 = (s00 + s11) / np.sqrt(2)


def create_bell_pair(node: Node):
    q1, q2 = ns.qubits.create_qubits(2)
    ns.qubits.combine_qubits([q1, q2])
    node.qmemory.put([q1, q2])
    # ns.qubits.operate(q1, ns.H)


def create_physical_network() -> Network:
    network = Network("Network with repeater")

    node_A = Node("A")
    node_B = Node("B")
    repeater = Node("Repeater")

    node_A.add_subcomponent(QSource(name="QSource_A", state_sampler=StateSampler([b00]),
                                    status=SourceStatus.EXTERNAL, int_num_ports=2))
    node_B.add_subcomponent(QSource(name="QSource_B", state_sampler=StateSampler([b00]),
                                    status=SourceStatus.EXTERNAL, int_num_ports=2))

    # ports for qmemory communication
    node_A.subcomponents["QSource_A"].add_ports(["qout1"])
    node_B.subcomponents["QSource_B"].add_ports(["qout1"])

    # TODO: fallback to nonphysical?
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

    # alice.subcomponents["QuantumSourceAlice"].ports["qout0"].forward_output(alice.ports[port_alice])
    # alice.subcomponents["QuantumSourceAlice"].ports["qout1"].connect(alice.qmemory.ports["qin0"])
    # bob.ports[port_bob].forward_input(bob.qmemory.ports["qin0"])

    # link qsource input port to qmemory output port and vice versa
    node_A.subcomponents["QSource_A"].ports["qout1"].connect(node_A.qmemory.ports["qin0"])
    node_B.subcomponents["QSource_B"].ports["qout1"].connect(node_B.qmemory.ports["qin0"])

    repeater.ports[portRA].forward_input(repeater.qmemory.ports["qin0"])
    repeater.ports[portRB].forward_input(repeater.qmemory.ports["qin1"])
    return network


if __name__ == '__main__':
    network = create_physical_network()
    a = network.get_node("A")
    b = network.get_node("B")
    r = network.get_node("Repeater")

    # create_bell_pair(a)     # TODO: parallel the processes?
    # create_bell_pair(b)     # TODO: qubit generation should occur within qsource

    for i in range(100):
        a_protocol = EntangleNodes(on_node=a, is_source=True, name="a_protocol")
        r_protocol = EntangleNodes(on_node=r, is_source=False, name="r_protocol", input_mem_pos=0)

        a_protocol.start()
        r_protocol.start()

        sim_run()
        if a.qmemory.peek([1]) or a.qmemory.peek([0]):
            print(a.qmemory.peek([1]))

# rounds: creation of pairs, ";" -- next round

