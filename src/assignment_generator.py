import random
import numpy

def generate_aufgabe(mat):
    len_list =[100,150,200,250]
    random.seed(mat+1)
    len_ = random.choice(len_list)
    
    lane_list =[2,3]
    random.seed(mat+2)
    lane_ = random.choice(lane_list)
    
    uml_list =[60,90,120]
    random.seed(mat+3)
    uml_ = random.choice(uml_list)
    
    cars_list =[50, 75, 100]
    random.seed(mat+4)
    cars_ = random.choice(cars_list)
    
    mak_list =['average vehicles per edge',
               'average waiting time per edge',
               'average traffic density per edge']
    random.seed(mat+5)
    mak_ = random.choice(mak_list)
    
    
    print(f'''
    Your task in the first exercise will be to define a traffic network with 4 intersections/nodes (1),
    the edges between the nodes must have a length of {len_} meters (2). All edges should be
    drivable in both directions, and have {lane_} lanes per direction (3). Within the
    traffic network, it is not possible to turn. This means that at the intersections it is not possible to turn
    left or right (4).

    The intersections are equipped with traffic lights for traffic control (5). Each edge must turn green once during the phase cycle
    and each phase is followed by a corresponding yellow phase and a red phase of at least 3
    seconds each (6). In total, each traffic light must have a cycle time of {uml_} seconds (7).

    Further define a traffic demand of a total of {cars_} vehicles. A vehicle should start every 2 seconds in the simulation (8). The vehicles should
    start alternately at the outer edges of the traffic network in a clockwise direction (9).

    Then enable the simulation of the traffic demand within the traffic network using a
    SUMO config file (10).

    To determine the macroscopic traffic size - {mak_} - continue to create a
    Python script that conducts the simulation (11).
    Use traci within the script to determine the macroscopic traffic size
    - {mak_} - during the simulation (12). Use this Jupyter Notebook and the already prepared next cell for this.


     ''')
