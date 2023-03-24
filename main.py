import netsquid as ns
from netsquid.components import QuantumChannel, QuantumMemory, ClassicalChannel
from netsquid.nodes import Node, DirectConnection

# ( create(A~A) ; transmit(A~A to A~R)  ||
# create(B~B) ; transmit(B~B to B~R)  ) ; swap (A~R and B~R to AB).
# TODO: tilda at the last AB?


def create_bell_pair(node: Node):
    q1, q2 = ns.qubits.create_qubits(2)
    ns.qubits.combine_qubits([q1, q2])
    node.qmemory.put([q1, q2])


def create_physical_network() -> (Node, Node, Node):
    node_A = Node("A")
    node_B = Node("B")
    repeater = Node("Repeater")

    # TODO: two positions or the second qubit is instantly sent to the repeater?
    node_A.add_subcomponent(QuantumMemory(name="A_memory", num_positions=2))
    node_B.add_subcomponent(QuantumMemory(name="B_memory", num_positions=2))
    repeater.add_subcomponent(QuantumMemory(name="R_memory", num_positions=2))

    # channelAtoR_classical = ClassicalChannel(name="AtoR_channel_classical")
    # channelRtoA_classical = ClassicalChannel(name="RtoA_channel_classical")
    channelAtoR_quantum = QuantumChannel(name="AtoR_channel_quantum")  # one-directed channel?
    channelRtoA_quantum = QuantumChannel(name="RtoA_channel_quantum")

    # channelBtoR_classical = ClassicalChannel(name="BtoR_channel_classical")
    # channelRtoB_classical = ClassicalChannel(name="RtoB_channel_classical")
    channelBtoR_quantum = QuantumChannel(name="BtoR_channel_quantum")
    channelRtoB_quantum = QuantumChannel(name="RtoB_channel_quantum")

    # connectionA_R_classical = DirectConnection(name="AtoR_connection_c", channel_AtoB=channelAtoR_classical,
    #                                  channel_BtoA=channelRtoA_classical)
    # connectionB_R_classical = DirectConnection(name="BtoR_connection_c", channel_AtoB=channelBtoR_classical,
    #                                  channel_BtoA=channelRtoB_classical)
    connectionA_R_quantum = DirectConnection(name="AtoR_connection_q", channel_AtoB=channelAtoR_quantum,
                                             channel_BtoA=channelRtoA_quantum)
    connectionB_R_quantum = DirectConnection(name="BtoR_connection_q", channel_AtoB=channelBtoR_quantum,
                                             channel_BtoA=channelRtoB_quantum)

    # node_A.connect_to(remote_node=repeater, connection=connectionA_R_classical)
    # node_B.connect_to(remote_node=repeater, connection=connectionB_R_classical)
    node_A.connect_to(remote_node=repeater, connection=connectionA_R_quantum)
    node_B.connect_to(remote_node=repeater, connection=connectionB_R_quantum)

    return node_A, node_B, repeater


a, b, repeater = create_physical_network()
create_bell_pair(a)     # TODO: parallel the processes?
create_bell_pair(b)
# print(a.qmemory.peek(1))
# TODO: send the qubit to repeater and swap
