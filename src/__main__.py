from netsquid.components import INSTR_MEASURE_BELL, INSTR_X, INSTR_Z
from src.entangle_nodes import EntangleNodes, create_physical_network
from netsquid import sim_run

# ( create(A~A) ; transmit(A~A to A~R)  ||
# create(B~B) ; transmit(B~B to B~R)  ) ; swap (A~R and B~R to AB).


if __name__ == '__main__':
    network = create_physical_network()
    a = network.get_node("A")
    b = network.get_node("B")
    r = network.get_node("Repeater")

    a_protocol = EntangleNodes(on_node=a, is_source=True, name="a_protocol")
    r_protocol = EntangleNodes(on_node=r, is_source=False, name="r_protocol")

    a_protocol.start()
    r_protocol.start()

    sim_run()
    print("Qubit in repeater memory after A~R: ", r.qmemory.peek([0]))

    b_protocol = EntangleNodes(on_node=b, is_source=True, name="b_protocol")

    b_protocol.start()
    r_protocol.start()

    sim_run()
    print("Qubit in repeater memory after R~B: ", r.qmemory.peek([1]))
    # print("Qstate1:", a.qmemory.peek([0])[0].qstate)
    # print("Qstate1 qrepr:", a.qmemory.peek([0])[0].qstate.qrepr)

    # print("Qstate2:", b.qmemory.peek([0])[0].qstate)
    # print("Qstate2 qrepr:", b.qmemory.peek([0])[0].qstate.qrepr)

    measured = r.qmemory.execute_instruction(INSTR_MEASURE_BELL, output_key='M')
    cur_state = measured[0]['M'][0]

    if cur_state == 1:
        # |01>
        r.qmemory.execute_instruction(INSTR_X)
    elif cur_state == 2:
        # |11>
        r.qmemory.execute_instruction(INSTR_Z)
        r.qmemory.execute_instruction(INSTR_X)
    elif cur_state == 3:
        # |10>
        r.qmemory.execute_instruction(INSTR_Z)

    print("ket state after swapping: ", a.qmemory.peek([0])[0].qstate.qrepr)

    # print(r.qmemory.peek([0, 1]))


# ~/.pyenv/versions/3.10.7/lib/python3.10/site-packages/netsquid/docs
