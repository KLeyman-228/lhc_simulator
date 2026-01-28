import json

def fix_particle_symbols(data):
    """
    Исправляет неправильные символы частиц в данных JSON
    """
    symbol_corrections = {
        # Бозоны
        "Z0": "Z⁰",
        "Z": "Z⁰",
        
        # Мезоны (пионы, ро, омега, фи, эта)
        "e": "η",
        "e⁰": "η",
        "ρ⁰": "ρ⁰",
        "ρ⁺": "ρ⁺",
        "ρ⁻": "ρ⁻",
        "ω⁰": "ω⁰",
        "φ": "φ",
        "a₁⁰": "a₁(⁰",
        "a₁⁺": "a₁⁺",
        "a₁⁻": "a₁⁻",
        "f": "f₂⁰",
        "f₁⁰": "f₁⁰",
        "h₁⁰": "h₁⁰",
        
        # Каоны
        "K⁺": "K⁺",
        "K⁻": "K⁻",
        "K⁰": "K⁰",
        "K⁰": "K⁰",  # повтор для разных типов
        
        # D-мезоны
        "D": "D⁺",
        "d₁⁰": "D₁⁰",
        "d₁⁺": "D₁⁺",
        "d₁⁻": "D₁⁻",
        "dbar₁⁰": "D̄₁⁰",
        
        # B-мезоны
        "B": "B⁺",
        
        # Чармоний
        "χ_c": "χ_c0",
        "h": "h_c",
        "p": "ψ",
        "J": "J/ψ",
        
        # Боттомоний
        "χ_b": "χ_b0",
        "h": "h_b",
        "ϒ": "ϒ",
        "ϒ₂": "ϒ₂",
        
        # Нуклоны и гипероны
        "N⁰": "N⁰",
        "N⁺": "N⁺",
        "N⁻": "N⁻",
        "Δ⁰": "Δ⁰",
        "Δ⁺": "Δ⁺",
        "Δ⁻": "Δ⁻",
        "Λ⁰": "Λ⁰",
        "Σ⁺": "Σ⁺",
        "Σ⁰": "Σ⁰",
        "Σ⁻": "Σ⁻",
        
        # Общие исправления
        "π⁰": "π⁰",
        "π⁺": "π⁺",
        "π⁻": "π⁻",
        "f₀⁰": "f₀⁰",
        "f₂⁰": "f₂⁰",
        "f₄⁰": "f₄⁰",
    }
    
    for particle in data:
        name = particle["name"]
        current_symbol = particle.get("symbol", "")
        
        # Исправляем наиболее очевидные ошибки
        if current_symbol == "e" or current_symbol == "e⁰":
            if "eta" in name.lower():
                particle["symbol"] = "η"
                if "0" in name or "⁰" in name:
                    particle["symbol"] = "η⁰"
        
        elif current_symbol == "ρ⁰":
            if "rho" in name.lower() and "770" in name:
                particle["symbol"] = "ρ(770)⁰"
            elif "rho" in name.lower() and "1450" in name:
                particle["symbol"] = "ρ(1450)⁰"
            elif "rho" in name.lower() and "1700" in name:
                particle["symbol"] = "ρ(1700)⁰"
        
        elif current_symbol == "ω⁰":
            if "omega" in name.lower() and "782" in name:
                particle["symbol"] = "ω(782)⁰"
            elif "omega" in name.lower() and "1420" in name:
                particle["symbol"] = "ω(1420)⁰"
        
        elif current_symbol == "φ":
            if "phi" in name.lower() and "1020" in name:
                particle["symbol"] = "φ(1020)"
            elif "phi" in name.lower() and "1680" in name:
                particle["symbol"] = "φ(1680)"
        
        elif current_symbol == "D" and particle.get("charge", 0) == 1.0:
            particle["symbol"] = "D⁺"
        elif current_symbol == "D" and particle.get("charge", 0) == -1.0:
            particle["symbol"] = "D⁻"
        elif current_symbol == "D" and particle.get("charge", 0) == 0.0:
            particle["symbol"] = "D⁰"
        
        elif current_symbol == "B" and particle.get("charge", 0) == 1.0:
            particle["symbol"] = "B⁺"
        elif current_symbol == "B" and particle.get("charge", 0) == -1.0:
            particle["symbol"] = "B⁻"
        elif current_symbol == "B" and particle.get("charge", 0) == 0.0:
            particle["symbol"] = "B⁰"
        
        # Общий случай: если символ есть в словаре исправлений
        if current_symbol in symbol_corrections:
            # Проверяем, подходит ли исправление по имени частицы
            correction = symbol_corrections[current_symbol]
            if correction.startswith("ρ(") and "rho" not in name.lower():
                continue  # Пропускаем, если это не ро-мезон
            if correction.startswith("ω(") and "omega" not in name.lower():
                continue  # Пропускаем, если это не омега-мезон
            particle["symbol"] = correction
    
    return data

def main():
    # Загрузка данных
    with open('particles.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Исправление символов
    fixed_data = fix_particle_symbols(data)
    
    # Сохранение исправленных данных
    with open('particles_fixed.json', 'w', encoding='utf-8') as f:
        json.dump(fixed_data, f, ensure_ascii=False, indent=2)
    
    print(f"Исправлено {len(data)} записей. Результат сохранен в particles_fixed.json")

if __name__ == "__main__":
    main()