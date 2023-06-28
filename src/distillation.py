from netsquid import sim_run
from src.entangle_nodes import EntangleNodes
from netsquid.components import (
    INSTR_SWAP,
    INSTR_MEASURE_BELL
)
import netsquid.qubits.ketstates as ks
from netsquid.qubits import StateSampler
from src.topology import physical_network_noisy

# pA = [create(A~A) | | create(A~A)]; [transmit(A~A -> A~R) | | transmit(A~A -> A~R)];
# pB = [create(B~B) | | create(B~B)]; [transmit(B~B -> B~R) | | transmit(B~B -> B~R)];
# P2 = (pA || pB) ; [distill(2 x A~R to 1 x A~R)] ; [distill(2 x B~R to 1 x B~R)] ;


def distillation_experiment():
    network = physical_network_noisy(state_sampler=StateSampler([ks.b00, ks.b01]), b00_prob=0.8,
                                     mem_pos_qsource=2, mem_pos_repeater=4)
    a = network.get_node("A")
    b = network.get_node("B")
    r = network.get_node("Repeater")

    a_protocol = EntangleNodes(on_node=a, is_source=True, name="a_protocol")
    r_protocol = EntangleNodes(on_node=r, is_repeater=True, name="r_protocol")
    b_protocol = EntangleNodes(on_node=b, is_source=True, is_endnode=True, name="b_protocol")

    a_protocol.start()
    b_protocol.start()
    r_protocol.start()

    for i in range(2):
        sim_run()

        if i == 0:
            a.qmemory.execute_instruction(INSTR_SWAP)
            b.qmemory.execute_instruction(INSTR_SWAP)
            INSTR_SWAP.execute(quantum_memory=r.qmemory, positions=[0, 2])
            INSTR_SWAP.execute(quantum_memory=r.qmemory, positions=[1, 3])
            a_protocol.reset()
            b_protocol.reset()
            r_protocol.reset()

    # TODO: if fidelity between A~A is low --- regenerate the pair
    fidelity_A = r.qmemory.peek([2])[0].qstate.qrepr.fidelity(a.qmemory.peek([1])[0].qstate.qrepr)
    print("Fidelity measurement before entanglement: ", fidelity_A)

    INSTR_MEASURE_BELL.execute(quantum_memory=r.qmemory, positions=[0, 1])
    INSTR_MEASURE_BELL.execute(quantum_memory=r.qmemory, positions=[2, 3])

    fidelity_A = r.qmemory.peek([2])[0].qstate.qrepr.fidelity(r.qmemory.peek([3])[0].qstate.qrepr)
    print("Fidelity measurement before entanglement: ", fidelity_A)

