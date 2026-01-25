from particle import Particle
import pdg
import json

api = pdg.connect()

all_particles = []


def safe_mass(m):
    try:
        if m.mass is not None:
            return m.mass
        else:
            return 0
    except:
        return 0
    

def load_particles():
    for i in api.get_particles():
        a = api.get(i.pdgid)
        for particle in a:
            try:

                name = particle.name
                mass = safe_mass(particle)
                charge = particle.charge
                spin = particle.quantum_J
                mcid = particle.mcid

                if particle.mcid is None:
                    continue

                try:
                    item = Particle.from_pdgid(particle.mcid)
                    struct = item.quarks
                except:
                    struct = None

                if particle.is_lepton:
                    type = "lepton"
                    color = "#628F3F"
                elif particle.is_boson:
                    type = "boson"
                    color = "#BC9019"
                elif particle.is_baryon or particle.is_meson:
                    type = "hadron"
                    color = "#4E3F8F"                   
                else:
                    continue

                all_particles.append({
                    "name": name,
                    "descr": "",
                    "mass": mass,
                    "charge": charge,
                    "spin": spin,
                    "struct": struct,
                    "type": type,
                    "mcid": mcid,
                    "color": color
                })

            except Exception as e:
                print(e)
                continue

                

            

    print(f"Загружено {len(all_particles)} частиц")

load_particles()
with open('all_particles.json', 'w', encoding='utf-8') as f:
    json.dump(all_particles, f, ensure_ascii=False, indent=4)


    
