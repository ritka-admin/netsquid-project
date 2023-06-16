from netsquid import sim_run
from src.entangle_nodes import EntangleNodes
from netsquid.components import (
    QuantumChannel,
    QuantumProcessor,
    QSource,
    ClassicalChannel,
    SourceStatus,
    FixedDelayModel,
    DepolarNoiseModel,
    FibreDelayModel,
    INSTR_SWAP,
    INSTR_MEASURE_BELL
)
import netsquid.qubits.ketstates as ks
from netsquid.nodes.network import Network, Node, DirectConnection
from netsquid.qubits import StateSampler
from src.states import *


def create_physical_network(b00_prob) -> Network:
    network = Network("Network with repeater")

    node_A = Node("A")
    node_B = Node("B")
    repeater = Node("Repeater")

    node_A.add_subcomponent(QSource(name="QSource_A", state_sampler=StateSampler([ks.b00, ks.b01]),
                                    probabilities=[b00_prob, 1-b00_prob],
                                    status=SourceStatus.EXTERNAL, num_ports=2,
                                    models={"emission_delay_model": FixedDelayModel(1e5),
                                            "emission_noise_model": DepolarNoiseModel(time_independent=True, depolar_rate=0.5)}))

    node_B.add_subcomponent(QSource(name="QSource_B", state_sampler=StateSampler([ks.b00, ks.b01]),
                                    probabilities=[b00_prob, 1-b00_prob],
                                    status=SourceStatus.EXTERNAL, num_ports=2,
                                    models={"emission_noise_model": DepolarNoiseModel(time_independent=True, depolar_rate=0.5)}))

    # ports for qmemory communication
    node_A.subcomponents["QSource_A"].add_ports(["qout1"])
    node_B.subcomponents["QSource_B"].add_ports(["qout1"])

    node_A.add_subcomponent(QuantumProcessor(name="A_memory", num_positions=2, fallback_to_nonphysical=True
                                             , memory_noise_models=DepolarNoiseModel(1000)))
    node_B.add_subcomponent(QuantumProcessor(name="B_memory", num_positions=2, fallback_to_nonphysical=True
                                             , memory_noise_models=DepolarNoiseModel(1000)))
    repeater.add_subcomponent(QuantumProcessor(name="R_memory", num_positions=4, fallback_to_nonphysical=True))

    network.add_nodes([node_A, node_B, repeater])

    channelAtoR_classical = ClassicalChannel(name="AtoR_channel_classical",
                                             models={"delay_model": FibreDelayModel(c=200e3)})
    channelRtoA_classical = ClassicalChannel(name="RtoA_channel_classical",
                                             models={"delay_model": FibreDelayModel(c=200e3)})

    channelBtoR_classical = ClassicalChannel(name="BtoR_channel_classical")
    channelRtoB_classical = ClassicalChannel(name="RtoB_channel_classical")

    connectionA_R_classical = DirectConnection(name="AtoR_connection_c", channel_AtoB=channelAtoR_classical,
                                     channel_BtoA=channelRtoA_classical)
    connectionB_R_classical = DirectConnection(name="BtoR_connection_c", channel_AtoB=channelBtoR_classical,
                                     channel_BtoA=channelRtoB_classical)

    network.add_connection(node_A, repeater, connection=connectionA_R_classical)
    network.add_connection(node_B, repeater, connection=connectionB_R_classical)

    channelAtoR_quantum = QuantumChannel(name="AtoR_channel_quantum",
                                         length=20,
                                         models={"delay_model": FibreDelayModel(c=200e3),
                                                 "noise_model": DepolarNoiseModel(500)})
    channelBtoR_quantum = QuantumChannel(name="BtoR_channel_quantum",
                                         length=20,
                                         models={"delay_model": FibreDelayModel(c=200e3)})

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


if __name__ == '__main__':
    network = create_physical_network(b00_prob=0.8)
    a = network.get_node("A")
    b = network.get_node("B")
    r = network.get_node("Repeater")

    a_protocol = EntangleNodes(on_node=a, is_source=True, name="a_protocol")
    r_protocol = EntangleNodes(on_node=r, is_repeater=True, name="r_protocol")
    b_protocol = EntangleNodes(on_node=b, is_source=True, is_endnode=True, name="b_protocol")

    # pA = [create(A~A) | | create(A~A)]; [transmit(A~A -> A~R) | | transmit(A~A -> A~R)];
    # [distill(2 x A~R to 1 x A~R)]

    # pB = [create(B~B) | | create(B~B)]; [transmit(B~B -> B~R) | | transmit(B~B -> B~R)];
    # [distill(2 x B~R to 1 x B~R)]
    for i in range(2):
        a_protocol.start()
        b_protocol.start()
        r_protocol.start()
        sim_run()

        if i == 0:
            a.qmemory.execute_instruction(INSTR_SWAP)
            b.qmemory.execute_instruction(INSTR_SWAP)
            INSTR_SWAP.execute(quantum_memory=r.qmemory, positions=[0, 2])
            INSTR_SWAP.execute(quantum_memory=r.qmemory, positions=[1, 3])

    # TODO: where to put noise model (source, processor, channel)
    # TODO: fidelity2 is always 1.0
    print(a.qmemory.peek([1])[0].qstate.qrepr)
    print(r.qmemory.peek([2])[0].qstate.qrepr)
    print(r.qmemory.peek([0, 1, 2, 3]))
    fidelity_A = r.qmemory.peek([2])[0].qstate.qrepr.fidelity(a.qmemory.peek([1])[0].qstate.qrepr)
    print("1: ", fidelity_A)

    INSTR_MEASURE_BELL.execute(quantum_memory=r.qmemory, positions=[0, 1])
    INSTR_MEASURE_BELL.execute(quantum_memory=r.qmemory, positions=[2, 3])

    fidelity_A = r.qmemory.peek([2])[0].qstate.qrepr.fidelity(r.qmemory.peek([3])[0].qstate.qrepr)
    print("2: ", fidelity_A)
    # print("qrepr: ", r.qmemory.peek([2])[0].qstate.qrepr)

    # distill( 2 x B~R to 1 x B~R)
    #  pB ; [ (if distill B~R fails then rerun pB) until distill B~R succeeds]  ] ;
    # [ swap(at R to A~B) ]
