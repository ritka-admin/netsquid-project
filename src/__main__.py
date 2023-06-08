from netsquid import sim_run
from netsquid.components import INSTR_MEASURE_BELL
from src.entangle_nodes import EntangleNodes, create_physical_network, perform_correction
from netsquid.qubits.dmutil import partialtrace

# ( create(A~A) ; transmit(A~A to A~R)  ||
# create(B~B) ; transmit(B~B to B~R)  ) ; swap (A~R and B~R to AB).


if __name__ == '__main__':
    network = create_physical_network()
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

    # print("BEFORE, ket state after swapping, nodeA: ", a.qmemory.peek([0])[0].qstate.qrepr)
    # print("BEFORE, ket state after swapping, nodeB: ", b.qmemory.peek([0])[0].qstate.qrepr)

    measuredB = r.qmemory.execute_instruction(INSTR_MEASURE_BELL, output_key='B')
    cur_stateB = measuredB[0]['B'][0]

    # print("MeasuredB: ", measuredB)

    perform_correction(b, cur_stateB)

    # find the qrepr of two qubits instead of the 4 in total (not interested in the repeater) --- partial trace
    # print("AFTER, ket state after swapping, nodeA: ", a.qmemory.peek([0])[0].qstate.qrepr)
    # print("AFTER, ket state after swapping, nodeB: ", b.qmemory.peek([0])[0].qstate.qrepr)

    density_matrix = a.qmemory.peek([0])[0].qstate.qrepr.reduced_dm()
    traced = partialtrace(density_matrix, [0, 3])  # TODO: qubits numbers? may differ from time to time?
    print(traced)

# ~/.pyenv/versions/3.10.7/lib/python3.10/site-packages/netsquid/docs
