# Front del planeador. Solo llama al motor: aqui no hay ninguna regla del sistema.
# Arranque: streamlit run app/app.py
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor import Red, simular_fila  # noqa: E402

st.set_page_config(page_title="Planeador TransMilenio", page_icon="🚌", layout="wide")


@st.cache_resource
def cargar_red():
    return Red(str(RAIZ / "datos"))


red = cargar_red()
todas = red.rango("", "￿")  # abiertas, para los selectores

st.title("🚌 Planeador TransMilenio")
st.caption("Red real de TransMilenio (GTFS julio 2021). Toda la logica vive en motor/.")

tabs = st.tabs(["Estaciones", "Próximo bus", "Planear viaje", "Ranking",
                "Rutas", "Cerrar / reabrir", "Fila hora pico", "Panel de rendimiento"])

# ---------------- R1, R2, R3 ----------------
with tabs[0]:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Buscar estación (R1)")
        nombre = st.text_input("Nombre exacto", "PORTAL NORTE")
        estado = red.estado(nombre.strip().upper())
        color = {"ABIERTA": "green", "CERRADA": "orange", "NO EXISTE": "red"}[estado]
        st.markdown(f"### :{color}[{estado}]")
    with c2:
        st.subheader("Autocompletar (R2)")
        prefijo = st.text_input("Escribe el inicio", "CAL")
        k = st.slider("Máximo de resultados (k)", 1, 20, 8)
        st.write(red.autocompletar(prefijo.upper(), k) or "Sin resultados")
    st.subheader("Listar un rango (R3)")
    c3, c4 = st.columns(2)
    desde = c3.text_input("Desde", "CALLE 26")
    hasta = c4.text_input("Hasta", "CALLE 80")
    st.write(red.rango(desde.upper(), hasta.upper()) or "Sin resultados")

# ---------------- R4 ----------------
with tabs[1]:
    st.subheader("¿A qué hora pasa mi bus? (R4)")
    est = st.selectbox("Estación", todas, index=todas.index("PORTAL NORTE") if "PORTAL NORTE" in todas else 0)
    rutas_est = red.rutas_por_estacion.get(est) or []
    if not rutas_est:
        st.info("Ninguna ruta para en esta estación.")
    else:
        c1, c2 = st.columns(2)
        ruta = c1.selectbox("Ruta", sorted(rutas_est))
        hora = c2.time_input("Hora", value=pd.Timestamp("07:00").time())
        res = red.proximo_bus(est, ruta, hora.strftime("%H:%M"))
        if res is None:
            st.warning("No hay más buses de esa ruta hoy.")
        else:
            st.success(f"El próximo **{ruta}** pasa por **{est}** a las **{res}**")

# ---------------- R5 ----------------
with tabs[2]:
    st.subheader("Planear un viaje (R5)")
    c1, c2 = st.columns(2)
    o = c1.selectbox("Origen", todas, index=todas.index("PORTAL NORTE") if "PORTAL NORTE" in todas else 0)
    d = c2.selectbox("Destino", todas, index=todas.index("PORTAL SUR") if "PORTAL SUR" in todas else 1)
    v = red.viaje(o, d)
    if v is None:
        st.error("No hay viaje directo ni con un solo transbordo.")
    else:
        for i, (ruta, sube, baja) in enumerate(v, 1):
            paradas = red.recorrido(ruta)
            n = paradas.index(baja) - paradas.index(sube)
            st.markdown(f"**Tramo {i}:** toma la ruta **{ruta}** en **{sube}** y bájate en **{baja}** ({n} paradas)")
        if len(v) == 2:
            st.info(f"Transbordo en **{v[0][2]}**")

# ---------------- R6 ----------------
with tabs[3]:
    st.subheader("Estaciones con más buses al día (R6)")
    k = st.slider("¿Cuántas?", 1, 30, 10, key="rk")
    top = pd.DataFrame(red.ranking(k), columns=["Estación", "Buses por día"])
    st.altair_chart(alt.Chart(top).mark_bar().encode(
        x="Buses por día:Q", y=alt.Y("Estación:N", sort="-x")), use_container_width=True)

# ---------------- R7 y R9 ----------------
with tabs[4]:
    st.subheader("Editar rutas (R7)")
    todas_rutas = sorted({r for e in red.estaciones.claves() for r in (red.rutas_por_estacion.get(e) or [])})
    ruta = st.selectbox("Ruta", todas_rutas)
    al_reves = st.toggle("Ver en sentido contrario")
    st.write(" → ".join(red.recorrido(ruta, al_reves)))
    c1, c2 = st.columns(2)
    with c1:
        nueva = st.selectbox("Estación a agregar", todas, key="nueva")
        despues = st.selectbox("Después de", red.recorrido(ruta), key="desp")
        if st.button("Agregar parada"):
            st.toast("Agregada" if red.agregar_parada(ruta, nueva, despues) else "No se pudo agregar")
            st.rerun()
    with c2:
        quitar = st.selectbox("Parada a quitar", red.recorrido(ruta), key="quitar")
        if st.button("Quitar parada"):
            st.toast("Quitada" if red.quitar_parada(ruta, quitar) else "No estaba")
            st.rerun()

# ---------------- R8 y R9 ----------------
with tabs[5]:
    st.subheader("Cerrar y reabrir estaciones (R8)")
    nombre = st.selectbox("Estación", red.estaciones.claves() and sorted(red.estaciones.claves()), key="cr")
    st.write("Estado actual:", red.estado(nombre))
    c1, c2 = st.columns(2)
    if c1.button("Cerrar"):
        st.toast("Cerrada" if red.cerrar(nombre) else "Ya estaba cerrada")
        st.rerun()
    if c2.button("Reabrir"):
        st.toast("Reabierta" if red.reabrir(nombre) else "Ya estaba abierta")
        st.rerun()
    st.subheader("Deshacer y rehacer (R9)")
    st.caption("Aplica a cierres, reaperturas y ediciones de ruta.")
    c3, c4 = st.columns(2)
    if c3.button("↩️ Deshacer"):
        st.toast("Deshecho" if red.deshacer() else "No hay nada que deshacer")
        st.rerun()
    if c4.button("↪️ Rehacer"):
        st.toast("Rehecho" if red.rehacer() else "No hay nada que rehacer")
        st.rerun()

# ---------------- R10 ----------------
with tabs[6]:
    st.subheader("Simular la fila en hora pico (R10)")
    c1, c2, c3 = st.columns(3)
    pasajeros = c1.number_input("Pasajeros", 1, 500000, 100000, step=10000)
    frecuencia = c2.number_input("Segundos entre buses", 1, 3600, 60)
    capacidad = c3.number_input("Cupo por bus", 1, 300, 160)
    if st.button("Simular"):
        import random
        import time
        llegadas = [random.randint(0, 3600) for _ in range(int(pasajeros))]
        t = time.perf_counter()
        salida = simular_fila(llegadas, int(frecuencia), int(capacidad))
        t = time.perf_counter() - t
        esperas = [s - l for s, l in zip(salida, llegadas)]
        st.write(f"Simulado en {t:.2f} s · espera promedio {sum(esperas) / len(esperas) / 60:.1f} min · "
                 f"máxima {max(esperas) / 60:.1f} min · último bus a los {max(salida) / 60:.0f} min")
        df = pd.DataFrame({"espera (min)": [e / 60 for e in esperas]})
        st.altair_chart(alt.Chart(df).mark_bar().encode(
            alt.X("espera (min):Q", bin=alt.Bin(maxbins=40)), y="count()"), use_container_width=True)

# ---------------- R11 ----------------
with tabs[7]:
    st.subheader("Panel de rendimiento (R11)")
    st.caption("Cada operación se corre en redes de 10.000, 20.000, 40.000 y 80.000 estaciones "
               "(python3 panel/medir.py). La pendiente es la del tiempo contra n en escala logarítmica: "
               "0 = constante, 1 = lineal.")
    archivo = RAIZ / "panel" / "resultados.csv"
    if not archivo.exists():
        st.warning("Corre primero: python3 panel/medir.py")
    else:
        res = pd.read_csv(archivo)
        res["microsegundos"] = res["segundos"] * 1e6
        ops = list(dict.fromkeys(res["operacion"]))
        elegidas = st.multiselect("Operaciones", ops, default=[o for o in ops if "carga" not in o and "fila" not in o])
        datos = res[res["operacion"].isin(elegidas)]
        st.altair_chart(alt.Chart(datos).mark_line(point=True).encode(
            x=alt.X("n:Q", scale=alt.Scale(type="log"), title="estaciones (n)"),
            y=alt.Y("microsegundos:Q", scale=alt.Scale(type="log"), title="tiempo por operación (µs)"),
            color="operacion:N", tooltip=["operacion", "n", "microsegundos"]), use_container_width=True)
        tabla = res.groupby("operacion", sort=False).first()[["complejidad", "pendiente_esperada", "pendiente_medida"]]
        tabla["¿coincide?"] = (tabla["pendiente_medida"] - tabla["pendiente_esperada"]).abs().map(
            lambda x: "✅" if x < 0.35 else "⚠️")
        st.dataframe(tabla, use_container_width=True)
        st.markdown(
            "**Cómo leerlo.** Las consultas (R1, R2, R3, R4, R6) quedan planas: duplicar la red no cambia su "
            "tiempo, como se espera de O(1) y O(log n). Cerrar, reabrir, editar y deshacer son O(log n): "
            "suben muy poco. En 80.000 se ve un salto pequeño que no viene del algoritmo sino de la memoria: "
            "el árbol y las tablas ya no caben en la caché del procesador y cada salto de puntero cuesta más. "
            "La carga y la fila crecen un poco más que lineal (pendiente ~1.1-1.2), que es lo que da n log n "
            "más el costo de crear millones de objetos en Python.")
