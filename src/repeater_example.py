from netsquid import sim_run
from netsquid.components import INSTR_MEASURE_BELL
from src.entangle_nodes import EntangleNodes, perform_correction
from src.topology import physical_network_noiseless
from netsquid.qubits.dmutil import partialtrace
from netsquid.qubits import StateSampler
import netsquid.qubits.ketstates as ks

# ( create(A~A) ; transmit(A~A to A~R)  ||
# create(B~B) ; transmit(B~B to B~R)  ) ; swap (A~R and B~R to AB).


def repeater_experiment():
    network = physical_network_noiseless(StateSampler([ks.b00]), distance=25,
                                         mem_pos_qsource=2, mem_pos_repeater=2)
    a = network.get_node("A")
    b = network.get_node("B")
    r = network.get_node("Repeater")

    a_protocol = EntangleNodes(on_node=a, is_source=True, name="a_protocol")
    r_protocol = EntangleNodes(on_node=r, is_repeater=True, name="r_protocol")
    b_protocol = EntangleNodes(on_node=b, is_endnode=True, is_source=True, name="b_protocol")

    a_protocol.start()
    b_protocol.start()
    r_protocol.start()

    sim_run()

    density_matrix = a.qmemory.peek([0])[0].qstate.dm
    traced1 = partialtrace(density_matrix, [0])
    print("Before entanglement: ", traced1)

    measuredB = r.qmemory.execute_instruction(INSTR_MEASURE_BELL, output_key='B')
    cur_stateB = measuredB[0]['B'][0]

    perform_correction(b, cur_stateB)

    density_matrix = a.qmemory.peek([0])[0].qstate.dm
    print(a.qmemory.peek([0])[0].qstate.qubits)
    traced = partialtrace(density_matrix, [0, 2])
    print("2: ", traced)

# ~/.pyenv/versions/3.10.7/lib/python3.10/site-packages/netsquid/docs
