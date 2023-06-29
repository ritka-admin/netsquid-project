from netsquid.components import (
    QuantumChannel,
    QuantumProcessor,
    QSource,
    ClassicalChannel,
    SourceStatus,
    FixedDelayModel,
    DepolarNoiseModel,
    FibreDelayModel,
)
from netsquid.qubits import StateSampler
from netsquid.nodes.network import Network, Node, DirectConnection


def physical_network_noiseless(
        state_sampler: StateSampler,
        distance: int,
        mem_pos_qsource: int,
        mem_pos_repeater: int
) -> Network:
    network = Network("Network with repeater")

    node_A = Node("A")
    node_B = Node("B")
    repeater = Node("Repeater")

    node_A.add_subcomponent(QSource(name="QSource_A", state_sampler=state_sampler,
                                    status=SourceStatus.EXTERNAL, num_ports=2))
    node_B.add_subcomponent(QSource(name="QSource_B", state_sampler=state_sampler,
                                    status=SourceStatus.EXTERNAL, num_ports=2))

    # ports for qmemory communication
    node_A.subcomponents["QSource_A"].add_ports(["qout1"])
    node_B.subcomponents["QSource_B"].add_ports(["qout1"])

    node_A.add_subcomponent(QuantumProcessor(name="A_memory", num_positions=mem_pos_qsource, fallback_to_nonphysical=True))
    node_B.add_subcomponent(QuantumProcessor(name="B_memory", num_positions=mem_pos_qsource, fallback_to_nonphysical=True))
    repeater.add_subcomponent(QuantumProcessor(name="R_memory", num_positions=mem_pos_repeater, fallback_to_nonphysical=True))

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

    channelAtoR_quantum = QuantumChannel(name="AtoR_channel_quantum", length=distance)
    channelBtoR_quantum = QuantumChannel(name="BtoR_channel_quantum", length=distance)

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


def physical_network_noisy(
        state_sampler: StateSampler,
        b00_prob: float,
        mem_pos_qsource: int,
        mem_pos_repeater: int
) -> Network:
    network = Network("Network with repeater")

    node_A = Node("A")
    node_B = Node("B")
    repeater = Node("Repeater")

    node_A.add_subcomponent(QSource(name="QSource_A", state_sampler=state_sampler,
                                    probabilities=[b00_prob, 1-b00_prob],
                                    status=SourceStatus.EXTERNAL, num_ports=2,
                                    models={"emission_delay_model": FixedDelayModel(1e5),
                                            "emission_noise_model": DepolarNoiseModel(time_independent=True,
                                                                                      depolar_rate=0.1)}))

    node_B.add_subcomponent(QSource(name="QSource_B", state_sampler=state_sampler,
                                    probabilities=[b00_prob, 1-b00_prob],
                                    status=SourceStatus.EXTERNAL, num_ports=2,
                                    models={"emission_noise_model": DepolarNoiseModel(time_independent=True,
                                                                                      depolar_rate=0.1)}))

    # ports for qmemory communication
    node_A.subcomponents["QSource_A"].add_ports(["qout1"])
    node_B.subcomponents["QSource_B"].add_ports(["qout1"])

    node_A.add_subcomponent(QuantumProcessor(name="A_memory", num_positions=mem_pos_qsource, fallback_to_nonphysical=True
                                             , memory_noise_models=DepolarNoiseModel(1000)))
    node_B.add_subcomponent(QuantumProcessor(name="B_memory", num_positions=mem_pos_qsource, fallback_to_nonphysical=True
                                             , memory_noise_models=DepolarNoiseModel(1000)))
    repeater.add_subcomponent(QuantumProcessor(name="R_memory", num_positions=mem_pos_repeater, fallback_to_nonphysical=True))

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
