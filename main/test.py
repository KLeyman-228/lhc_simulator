
import json
from LHC_Simulator import SimulationEvent, load_particles


Load_particle = False

test_json = json.dumps([
{
    "id_1": 2212,
    "id_2": 2212,
    "Energy": 70,
}
])


def get_inputs(request):
    global Received_particles

    inputs = json.loads(test_json)[0]

    Results = Collide_Simulation(inputs)

    return Results


def LoadAll():

    global Load_particle

    if Load_particle is False:
        particle_list, resonances = load_particles()
        Load_particle == True
        return particle_list, resonances



def Collide_Simulation(options):

    particle_list, resonances = LoadAll()

    id_1 = options['id_1']
    id_2 = options['id_2']
    E = options['Energy']

    finals, first_finals, values, init = SimulationEvent(
        id_1, id_2, E, particle_list, resonances
    )
    
    # Формируем результат
    result = [
        finals,
        first_finals,
        values,
        init
    ]


    Result = result
    with open('Result.json', 'w', encoding='utf-8') as f:
        json.dump(Result, f, ensure_ascii=False, indent=4)
    
    return Result

get_inputs(0)


"""
JSON:
[
{
    "id_1": 2212,
    "id_2": 2212,
    "Energy": 40,
}
]


JSON:
[
Первая ступень:
{
    "id_1": 2212,
    "id_2": 2212,
}
Распад:
{
    "id_1": 2212,
    "id_2": 2212,
    "id_3": 2212,
    ...
}
Значения:
{
    "Mass": 12.678,
    "BaryonNum": 2,
    "S,B,C": [0, 0, 1],
    "Charge": "+2",

}
]
"""
