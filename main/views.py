from rest_framework.decorators import api_view
from rest_framework.response import Response
import json
from django.http import JsonResponse
from .LHC_Simulator import SimulationEvent, load_particles


Load_particle = False



@api_view(['POST'])
def get_inputs(request):

    inputs = json.loads(request.body.decode('utf-8'))[0]

    Results = Collide_Simulation(inputs)

    return JsonResponse(Results, safe=False)


def LoadAll():

    global Load_particle

    if Load_particle is False:
        particle_list, resonances = load_particles()
        Load_particle = True
        return particle_list, resonances
    else:
        return particle_list, resonances



def Collide_Simulation(options):

    particle_list, resonances = LoadAll()

    id_1 = options['id_1']
    id_2 = options['id_2']
    E = options['Energy']

    finals, first_finals, values = SimulationEvent(id_1, id_2, E, particle_list, resonances)


    Result = [finals, first_finals, values]
    #print(Result)
    
    return Result




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
