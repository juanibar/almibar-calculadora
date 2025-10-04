
# streamlit_almibares.py
# Author: ChatGPT for Juan Ignacio (NoSoyNormal Cervecería)
# Exact sugar syrup calculator with physically grounded volume contraction.
# Assumptions: 20 °C, sucrose + water only. Uses partial specific volume of sucrose in water.

import math
import streamlit as st

st.set_page_config(page_title="Calculadora de Almíbares (Exacta)", page_icon="🥤", layout="centered")

# ---- CONSTANTES (20 °C) ----
# Densidad del agua a 20 °C (g/mL). Fuente típica de laboratorio ~0.9982 g/mL
RHO_WATER_20C = 0.9982

# Volumen específico parcial de la sacarosa en agua a ~20–25 °C (mL/g).
# Valores reportados en literatura: ~0.630–0.635 mL/g. Usamos 0.632 mL/g como valor central.
# Este valor permite modelar la contracción de volumen al disolver el azúcar.
V_SPECIFIC_SUCROSE = 0.632

# ---- UTILIDADES ----
def mass_fractions_from_ratio(sugar_to_water_ratio: tuple[int, int]) -> float:
    """
    Convierte una razón azúcar:agua (por masa) en fracción másica de azúcar (w_sugar).
    Ej.: (1,1) -> w=0.5 ; (2,1) -> w≈0.6667 ; (1,2) -> w≈0.3333
    """
    a, b = sugar_to_water_ratio
    total = a + b
    return a / total

def masses_for_target_volume(final_volume_ml: float, w_sugar: float,
                             rho_water_g_per_ml: float = RHO_WATER_20C,
                             v_sugar_ml_per_g: float = V_SPECIFIC_SUCROSE) -> tuple[float, float, float]:
    """
    Dado un volumen final deseado (mL) y la fracción másica de azúcar (w_sugar),
    calcula las masas exactas de solución total, azúcar y agua que producen ese volumen final,
    modelando la contracción de volumen con el volumen específico parcial del azúcar.

    V_final = M_total * ( w_sugar * v_sugar + (1 - w_sugar) / rho_water )
    => M_total = V_final / ( w_sugar * v_sugar + (1 - w_sugar) / rho_water )

    Retorna: (M_total_g, M_sugar_g, M_water_g)
    """
    denom = (w_sugar * v_sugar_ml_per_g) + ((1.0 - w_sugar) / rho_water_g_per_ml)
    m_total_g = final_volume_ml / denom
    m_sugar_g = w_sugar * m_total_g
    m_water_g = (1.0 - w_sugar) * m_total_g
    return m_total_g, m_sugar_g, m_water_g

def volume_from_masses(m_sugar_g: float, m_water_g: float,
                       rho_water_g_per_ml: float = RHO_WATER_20C,
                       v_sugar_ml_per_g: float = V_SPECIFIC_SUCROSE) -> float:
    """
    Calcula el volumen final (mL) de la mezcla agua + sacarosa a partir de las masas,
    aplicando el modelo de volumen parcial:
    V = (m_water / rho_water) + (m_sugar * v_sugar)
    """
    v_final_ml = (m_water_g / rho_water_g_per_ml) + (m_sugar_g * v_sugar_ml_per_g)
    return v_final_ml

def solution_density_g_per_ml(m_total_g: float, v_final_ml: float) -> float:
    """Densidad efectiva de la solución (g/mL)."""
    return m_total_g / v_final_ml if v_final_ml > 0 else float("nan")

def fmt_mass(g: float) -> str:
    if g >= 1000:
        return f"{g/1000:.3f} kg"
    return f"{g:.1f} g"

def fmt_volume(ml: float) -> str:
    if ml >= 1000:
        return f"{ml/1000:.3f} L"
    return f"{ml:.1f} mL"

# ---- UI ----
st.title("🥤 Calculadora de Almíbares (Exacta)")
st.caption("Modelo físico-químico con contracción de volumen (20 °C). Ratios **por masa** para precisión.")

with st.expander("📎 Notas técnicas (importante)", expanded=False):
    st.markdown(
        """
- **Definición de °Brix**: % en masa de sacarosa en solución. Si la solución es sólo agua+sacarosa, °Brix = 100·(masa de azúcar / masa total).
- **Contracción de volumen**: al disolver azúcar, el volumen final **no** es la suma de volúmenes. Se modela usando el **volumen específico parcial** de la sacarosa en agua (0.632 mL/g, ~20–25 °C) y la densidad del agua a 20 °C (0.9982 g/mL).
- **Ratios**: se interpretan como **azúcar:agua por masa** para asegurar exactitud. Si querés variantes por volumen, agregamos un modo aparte (con advertencias) en una versión futura.
- **Temperatura**: los cálculos están referidos a 20 °C. Cambios modestos de temperatura introducen errores menores en uso habitual.
        """
    )

mode = st.radio("Elegí el modo de cálculo:", ["A) Quiero un volumen final", "B) Tengo azúcar y agua (masas)"], index=0)

ratio_map = {
    "Almíbar 1:2": (1, 2),
    "Almíbar 1:1 (simple)": (1, 1),
    "Almíbar 2:1": (2, 1),
}

if mode.startswith("A"):
    col1, col2 = st.columns(2)
    with col1:
        ratio_label = st.selectbox("Proporción por **masa** (azúcar:agua)", list(ratio_map.keys()), index=1)
        ratio = ratio_map[ratio_label]
        w = mass_fractions_from_ratio(ratio)
        brix = 100 * w
        st.write(f"**°Brix objetivo ≈ {brix:.2f} °Bx**")

    with col2:
        unit = st.selectbox("Unidad del volumen final deseado", ["mL", "L"], index=0)
        v_value = st.number_input("Volumen final deseado", min_value=0.0, value=1000.0, step=10.0)
        v_final_ml = v_value * (1000.0 if unit == "L" else 1.0)

    m_total_g, m_sugar_g, m_water_g = masses_for_target_volume(v_final_ml, w)
    v_check_ml = volume_from_masses(m_sugar_g, m_water_g)
    rho = solution_density_g_per_ml(m_total_g, v_check_ml)

    st.subheader("Resultados")
    st.write(f"- Azúcar necesaria: **{fmt_mass(m_sugar_g)}**")
    st.write(f"- Agua necesaria: **{fmt_mass(m_water_g)}**  (≈ {fmt_volume(m_water_g / RHO_WATER_20C)} de agua)")
    st.write(f"- Densidad esperada de la mezcla: **{rho:.4f} g/mL**")
    st.write(f"- Contrachequeo volumen final: **{fmt_volume(v_check_ml)}** (debería coincidir con lo pedido)")
    st.write(f"- **°Brix final:** **{brix:.2f} °Bx**")

    with st.expander("Detalles del cálculo"):
        st.code(
            f"""
w (fracción másica de azúcar) = {w:.6f}
°Brix = 100·w = {brix:.4f}

Modelo de volumen final (20 °C):
V_final = M_total · ( w · v_sugar + (1 - w) / ρ_agua )

Despejando:
M_total = V_final / ( w · v_sugar + (1 - w) / ρ_agua )

Constantes usadas:
ρ_agua (20 °C) = {RHO_WATER_20C} g/mL
v_sugar (parcial) = {V_SPECIFIC_SUCROSE} mL/g
            """
        )

else:
    col1, col2 = st.columns(2)
    with col1:
        m_sugar_g = st.number_input("Masa de azúcar (g)", min_value=0.0, value=500.0, step=10.0)
        m_water_g = st.number_input("Masa de agua (g)", min_value=0.0, value=500.0, step=10.0)
    with col2:
        st.markdown("**Datos fijos (20 °C)**")
        st.write(f"- ρ(agua) = {RHO_WATER_20C} g/mL")
        st.write(f"- vₛ (sacarosa) = {V_SPECIFIC_SUCROSE} mL/g")

    m_total_g = m_sugar_g + m_water_g
    v_final_ml = volume_from_masses(m_sugar_g, m_water_g)
    rho = solution_density_g_per_ml(m_total_g, v_final_ml)
    w = m_sugar_g / m_total_g if m_total_g > 0 else float("nan")
    brix = 100 * w if not math.isnan(w) else float("nan")

    st.subheader("Resultados")
    st.write(f"- Volumen final esperado: **{fmt_volume(v_final_ml)}**")
    st.write(f"- Densidad de la mezcla: **{rho:.4f} g/mL**")
    st.write(f"- **°Brix final:** **{brix:.2f} °Bx**")

    with st.expander("Detalles del cálculo"):
        st.code(
            f"""
M_total = m_azúcar + m_agua = {m_total_g:.3f} g
V_final = (m_agua / ρ_agua) + (m_azúcar · v_sugar) = {v_final_ml:.3f} mL
ρ_solución = M_total / V_final = {rho:.5f} g/mL
w (fracción másica azúcar) = m_azúcar / M_total = {w:.6f}
°Brix = 100·w = {brix:.3f} °Bx
            """
        )

st.divider()
st.caption("© 2025 • Modelo basado en densidad del agua (20 °C) y volumen específico parcial de la sacarosa en agua (≈0.632 mL/g).")
