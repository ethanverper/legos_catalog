#from turtle import onclick
import streamlit as st
import pandas as pd
import io
import requests
#import streamlit.components.v1 as components
st.set_page_config(layout="wide")

# Initialize connection.
# Uses st.experimental_singleton to only run once.
if 'gs_URL' not in st.session_state:
    st.session_state.gs_URL = "https://docs.google.com/spreadsheets/d/1-IQY4SqCYFdOirg1KPP_AdtRtfXGkmgCEaXDFyRP098/export?format=csv&gid=0"

# URL de la hoja de Google en formato CSV
gs_URL = st.session_state.gs_URL

# Leer los datos directamente desde la URL CSV
df = pd.read_csv(gs_URL)

df2 = df
# if 'df' not in st.session_state:
#    st.session_state.df = df

df['Terminado'] = pd.to_datetime(df['Terminado'])

st.title('Project Table Catalog')

def local_css(file_name):
        st.markdown(
    """
    <style>
    .column {
  float: left;
  width: 33.33%;
}

/* Clear floats after the columns */
.row:after {
  content: "";
  display: table;
  clear: both;
}


.kpi.number {
  font-size: 2rem;
  text-align: center;
  color: rgb(90, 90, 90);
}

.kpi.text{
  font-size: 1rem;
  text-align: center;
  color: rgb(90, 90, 90);
  padding-top: 10px;
}

.tablebackground{
  background-color: #BAD2DE !important;
}


.viewbackground{
background-color: #CBE2DA !important;
}


.mvbackground{
background-color: #E5F0EC !important;
}


.smallheader{
    font-size: small !important;
}

#my-container {
  height: 100vh;
  width: 100%;
}
    </style>
    """, 
    unsafe_allow_html=True
)

def remote_css(url):
    st.markdown(f'<link href="{url}" rel="stylesheet">',
                unsafe_allow_html=True)

def header_bg(table_type):
    if table_type == "BASE TABLE":
        return "tablebackground"
    elif table_type == "VIEW":
        return "viewbackground"
    else:
        return "mvbackground"

remote_css(
    "https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.4.1/semantic.min.css")

local_css("style.css")
cb_view_details = st.sidebar.checkbox('View Details')

if cb_view_details:
    view_details=""
else:
    view_details="""style="display: none;" """

# Ordenar por
selectbox_orderby = st.sidebar.selectbox("Order By", ('A → Z', 'Z → A', 'Pasos ↓', 'Pasos ↑',
                                                      'Piezas ↓', 'Piezas ↑', 'Estatus'))

all_option = pd.Series(['All'])

# Inicialización de session_state si no está definida
if 'selectbox_industria' not in st.session_state:
    st.session_state.selectbox_empresa_key = 10
    st.session_state.selectbox_manual_key = 20
    st.session_state.selectbox_industria_key = 30
    st.session_state.selectbox_estatus_key = 40

# INDUSTRIA
fv_industria = df['Industria'].drop_duplicates()
fv_industria = pd.concat([fv_industria, all_option], ignore_index=True)
selectbox_industria = st.sidebar.selectbox(
    "Industria", fv_industria, len(fv_industria)-1, key=st.session_state.selectbox_industria_key)

if selectbox_industria != 'All':
    df = df.loc[df['Industria'] == selectbox_industria]
else:
    df = df.loc[df['Industria'].isin(fv_industria[:-1])]

# EMPRESA
fv_empresa = df['Empresa'].drop_duplicates()
fv_empresa = pd.concat([fv_empresa, all_option], ignore_index=True)  # Asegúrate de usar ignore_index

selectbox_empresa = st.sidebar.selectbox(
    'Empresa', fv_empresa, index=len(fv_empresa)-1, key=st.session_state.selectbox_empresa_key)

if selectbox_empresa != 'All':
    df = df.loc[df['Empresa'] == selectbox_empresa]
else:
    df = df.loc[df['Empresa'].isin(fv_empresa[:-1])]  # Corrección importante aquí

# MANUAL
fv_manual = df['Manual'].drop_duplicates()
fv_manual = pd.concat([fv_manual, all_option], ignore_index=True)  # Asegúrate de usar ignore_index

selectbox_manual = st.sidebar.selectbox(
    "Manual", fv_manual, len(fv_manual)-1, key=st.session_state.selectbox_manual_key)

if selectbox_manual != 'All':
    df = df.loc[df['Manual'] == selectbox_manual]
else:
    df = df.loc[df['Manual'].isin(fv_manual[:-1])]  # Corrección importante aquí

# ESTATUS (Multiselección)
fv_estatus = df['Estatus'].drop_duplicates()
selectbox_estatus = st.sidebar.multiselect(
    'Estatus', fv_estatus, default=fv_estatus, key=st.session_state.selectbox_estatus_key)

# Filtrar el DataFrame si se seleccionan opciones; si no, mostrar todo
if selectbox_estatus:
    df = df.loc[df['Estatus'].isin(selectbox_estatus)]

def reset_button():
    st.session_state.selectbox_empresa_key = st.session_state.selectbox_empresa_key+1
    st.session_state.selectbox_manual_key = st.session_state.selectbox_manual_key+1
    st.session_state.selectbox_industria_key = st.session_state.selectbox_industria_key+1
    st.session_state.selectbox_estatus_key = st.session_state.selectbox_estatus_key+1

clear_button = st.sidebar.button(
    label='Clear Selections', on_click=reset_button)

if clear_button:
    df = df2.copy()

# Card order
orderby_column = ''
orderby_asc = True

# Condiciones de ordenación
if selectbox_orderby == 'A → Z':
    orderby_column = 'Empresa'
    orderby_asc = True
elif selectbox_orderby == 'Z → A':
    orderby_column = 'Empresa'
    orderby_asc = False
elif selectbox_orderby == 'Pasos ↓':
    # Aquí ordenamos por el conteo de pasos (número de filas para cada 'Nombre')
    df['Paso Count'] = df.groupby('Nombre')['Paso'].transform('count')
    orderby_column = 'Paso Count'
    orderby_asc = False
elif selectbox_orderby == 'Pasos ↑':
    df['Paso Count'] = df.groupby('Nombre')['Paso'].transform('count')
    orderby_column = 'Paso Count'
    orderby_asc = True
elif selectbox_orderby == 'Piezas ↓':
    # Aquí ordenamos por la suma de piezas totales para cada 'Nombre'
    df['Total Piezas Sum'] = df.groupby('Nombre')['Total Piezas'].transform('sum')
    orderby_column = 'Total Piezas Sum'
    orderby_asc = False
elif selectbox_orderby == 'Piezas ↑':
    df['Total Piezas Sum'] = df.groupby('Nombre')['Total Piezas'].transform('sum')
    orderby_column = 'Total Piezas Sum'
    orderby_asc = True
elif selectbox_orderby == 'Estatus':
    orderby_column = 'Estatus'
    orderby_asc = False

# Ordenar el DataFrame basado en las condiciones definidas
df.sort_values(by=[orderby_column], inplace=True, ascending=orderby_asc)

# Filtros seleccionados por el usuario
selected_industria = st.session_state.get('selectbox_industria', 'All')
selected_empresa = st.session_state.get('selectbox_empresa', 'All')
selected_manual = st.session_state.get('selectbox_manual', 'All')
selected_estatus = st.session_state.get('selectbox_estatus', [])

# Filtrar el DataFrame según los valores seleccionados
pasos_totales = str(df['Paso'].count())
pasos_completos = str(df[df['Estatus'] == 'COMPLETO'].shape[0])
piezas_totales = str(df['Nombre'].nunique())
legos_totales = str(df['Total Piezas'].sum())
legos_distintos = str(df['Número de Piezas Distintas'].sum())

if selected_industria != 'All':
    df = df[df['Industria'] == selected_industria]
    pasos_totales = str(df[df['Industria'] == selected_industria]['Paso'].count())    
    pasos_completos = str(df[(df['Industria'] == selected_industria) & (df['Estatus'] == 'COMPLETO')].shape[0])
    piezas_totales = str(df[df['Industria'] == selected_industria]['Nombre'].nunique())
    legos_totales = str(df[df['Industria'] == selected_industria]['Total Piezas'].sum())
    legos_distintos = str(df[df['Industria'] == selected_industria]['Número de Piezas Distintas'].sum())

if selected_empresa != 'All':
    df = df[df['Empresa'] == selected_empresa]
    pasos_totales = str(df[df['Empresa'] == selected_empresa]['Paso'].count())    
    pasos_completos = str(df[(df['Empresa'] == selected_empresa) & (df['Estatus'] == 'COMPLETO')].shape[0])
    piezas_totales = str(df[df['Empresa'] == selected_empresa]['Nombre'].nunique())
    legos_totales = str(df[df['Empresa'] == selected_empresa]['Total Piezas'].sum())
    legos_distintos = str(df[df['Empresa'] == selected_empresa]['Número de Piezas Distintas'].sum())

if selected_manual != 'All':
    df = df[df['Manual'] == selected_manual]
    pasos_totales = str(df[df['Manual'] == selected_manual]['Paso'].count()) 
    pasos_completos = str(df[(df['Manual'] == selected_manual) & (df['Estatus'] == 'COMPLETO')].shape[0])
    piezas_totales = str(df[df['Manual'] == selected_manual]['Nombre'].nunique())
    legos_totales = str(df[df['Manual'] == selected_manual]['Total Piezas'].sum())
    legos_distintos = str(df[df['Manual'] == selected_manual]['Número de Piezas Distintas'].sum())
    
if selected_estatus:
    df = df[df['Estatus'].isin(selected_estatus)]
    pasos_totales = str(df[df['Estatus'] == selected_estatus]['Nombre'].count())

# Agrupar por la columna 'Piezas' para generar una tarjeta por cada tipo distinto
distinct_piezas = df['Nombre'].drop_duplicates()

table_scorecard = ""

table_scorecard += """
<div class="ui five small statistics">
  <div class="grey statistic">
    <div class="value">"""+pasos_totales+"""
    </div>
    <div class="grey label">
      Pasos Totales
    </div>
  </div>
    <div class="grey statistic">
        <div class="value">"""+pasos_completos+"""
        </div>
        <div class="label">
        Pasos Completos
        </div>
    </div>
    <div class="grey statistic">
        <div class="value">"""+legos_totales+"""
        </div>
        <div class="label">
        Legos Totales
        </div>
    </div>    
  <div class="grey statistic">
    <div class="value">
      """+legos_distintos+"""
    </div>
    <div class="label">
      Legos Distintos
    </div>
  </div>

  <div class="grey statistic">
    <div class="value">
      """+piezas_totales+"""
    </div>
    <div class="label">
      Figuras Totales
    </div>
  </div>
</div>"""

table_scorecard += """<br><br><br><div id="mydiv" class="ui centered cards">"""

directores = {"Honda": {"nombre_director" : "Garland Jeff", "nombre_empleados" : "Dani Fer"}, 
             "Eurotem": {"nombre_director" : "Omar Vallejo", "nombre_empleados" : "Dany Juárez"},
             "Tenant": {"nombre_director" : "Diana", "nombre_empleados" : "Ana Cris"},
             "Mulag": {"nombre_director" : "Alan Gold", "nombre_empleados" : "Alan Gold"},
             "SIKORSKI": {"nombre_director" : "Alex", "nombre_empleados" : "Hector Manuel"},
             "Airbus": {"nombre_director": "Lorena Gutierrez", "nombre_empleados": "Oscar Soto"},
             "Karmetciller": {"nombre_director" : "José de Jesús", "nombre_empleados": "Astryd"},
             "Brittania": {"nombre_director" : "Aldair", "nombre_empleados" : "Sandra Daniela"},
             "TDC": {"nombre_director" : "Jorge", "nombre_empleados" : "Miguel Suárez"},
             "UD Trucks": {"nombre_director" : "Miriam García", "nombre_empleados" : "Ale Chapa"},
             "Liebherr": {"nombre_director" : "Luis", "nombre_empleados": "Omar Vallejo"}}

trabajadores = {"Ale Chapa": {"pasos" : "", "legos_armados" : "", "empresas_trabajadas":"", "rol":""}, 
             "Miguel Suárez": {"pasos" : "", "legos_armados" : "", "empresas_trabajadas":"", "rol":""},
             "Dany Juárez": {"pasos" : "", "legos_armados" : "", "empresas_trabajadas":"", "rol":""},
             "Sandra Daniela": {"pasos" : "", "legos_armados" : "", "empresas_trabajadas":"", "rol":""},
             "Oscar Soto": {"pasos" : "", "legos_armados" : "", "empresas_trabajadas":"", "rol":""},
             "Hector Manuel": {"pasos" : "", "legos_armados" : "", "empresas_trabajadas":"", "rol":""},
             "Ana Cris": {"pasos" : "", "legos_armados" : "", "empresas_trabajadas":"", "rol":""},
             "Astryd": {"pasos" : "", "legos_armados" : "", "empresas_trabajadas":"", "rol":""},
             "Dani Fer": {"pasos" : "", "legos_armados" : "", "empresas_trabajadas":"", "rol":""},
             "Jorge Luis": {"pasos" : "", "legos_armados" : "", "empresas_trabajadas":"", "rol":""},
             "Omar Vallejo": {"pasos" : "", "legos_armados" : "", "empresas_trabajadas":"", "rol":""},
             "Lorena Gtz": {"pasos" : "", "legos_armados" : "", "empresas_trabajadas":"", "rol":""},
             "Miriam García": {"pasos" : "", "legos_armados" : "", "empresas_trabajadas":"", "rol":""},
             "José de Jesús": {"pasos" : "", "legos_armados" : "", "empresas_trabajadas":"", "rol":""},
             "Alan Gold": {"pasos" : "", "legos_armados" : "", "empresas_trabajadas":"", "rol":""},
             "Garland Jeff": {"pasos" : "", "legos_armados" : "", "empresas_trabajadas":"", "rol":""},
             "Aldair": {"pasos" : "", "legos_armados" : "", "empresas_trabajadas":"", "rol":""},
             "Luis Garcia": {"pasos" : "", "legos_armados" : "", "empresas_trabajadas":"", "rol":""},
             "Alex": {"pasos" : "", "legos_armados" : "", "empresas_trabajadas":"", "rol":""},
             "Pau": {"pasos" : "", "legos_armados" : "", "empresas_trabajadas":"", "rol":""},
             "Diana": {"pasos" : "", "legos_armados" : "", "empresas_trabajadas":"", "rol":""}}
             
import streamlit as st
import pandas as pd

# Función para asignar legos a empleados de manera equitativa
def asignar_legos(df_empresas, directores, empleados, porcentaje_director=0.2):
    asignaciones = {empleado: {'figuras': {}, 'total_piezas': 0} for empleado in empleados}

    # Fase 1: Calcular cuántas piezas tiene que armar cada empleado (equilibrado)
    total_legos_global = df_empresas['Total Piezas'].sum()
    piezas_por_empleado = total_legos_global // len(empleados)  # Piezas que cada empleado debería armar
    piezas_sobrantes = total_legos_global % len(empleados)

    # Fase 2: Asignar piezas primero en las empresas a sus empleados
    for (empresa, figura), group in df_empresas.groupby(['Empresa', 'Nombre']):
        total_legos_figura = group['Total Piezas'].sum()
        legos_director = int(total_legos_figura * porcentaje_director)
        legos_trabajadores = total_legos_figura - legos_director

        # Asignar al director las piezas
        directores[empresa]['legos_armados'] = legos_director

        # Obtener empleados de la empresa y repartir las piezas
        empleados_empresa = directores[empresa].get('nombre_empleados', "").split(", ")
        legos_por_empleado = legos_trabajadores // len(empleados_empresa) if empleados_empresa else 0
        legos_restantes = legos_trabajadores % len(empleados_empresa)

        # Asignar piezas a los empleados de la empresa
        for empleado in empleados_empresa:
            if empleado in asignaciones:
                piezas_a_asignar = min(legos_por_empleado, piezas_por_empleado - asignaciones[empleado]['total_piezas'])
                asignaciones[empleado]['figuras'][figura] = piezas_a_asignar
                asignaciones[empleado]['total_piezas'] += piezas_a_asignar

        # Distribuir las piezas restantes entre los empleados de la empresa
        for i in range(legos_restantes):
            empleado = empleados_empresa[i % len(empleados_empresa)]
            asignaciones[empleado]['figuras'][figura] += 1
            asignaciones[empleado]['total_piezas'] += 1

    # Fase 3: Redistribuir piezas para asegurar que todos los empleados trabajen en alguna figura
    empleados_faltantes = [emp for emp in empleados if asignaciones[emp]['total_piezas'] < piezas_por_empleado]  # Empleados que no han alcanzado su cuota
    piezas_disponibles = []

    # Revisar si hay piezas sobrantes para redistribuir de figuras ya asignadas
    for (empresa, figura), group in df_empresas.groupby(['Empresa', 'Nombre']):
        total_legos_figura = group['Total Piezas'].sum()
        piezas_asignadas = sum(info['figuras'].get(figura, 0) for info in asignaciones.values())

        if piezas_asignadas < total_legos_figura:
            piezas_restantes = total_legos_figura - piezas_asignadas
            piezas_disponibles.append((figura, piezas_restantes, empresa))

    # Asignar las piezas sobrantes de las figuras a empleados faltantes
    for figura, piezas_restantes, empresa in piezas_disponibles:
        for empleado in empleados_faltantes:
            if piezas_restantes > 0 and asignaciones[empleado]['total_piezas'] < piezas_por_empleado:
                piezas_a_asignar = min(piezas_por_empleado - asignaciones[empleado]['total_piezas'], piezas_restantes)
                if figura in asignaciones[empleado]['figuras']:
                    asignaciones[empleado]['figuras'][figura] += piezas_a_asignar
                else:
                    asignaciones[empleado]['figuras'][figura] = piezas_a_asignar

                asignaciones[empleado]['total_piezas'] += piezas_a_asignar
                piezas_restantes -= piezas_a_asignar

            if piezas_restantes == 0:
                break

    # Fase 4: Redistribuir cualquier exceso
    empleados_con_exceso = [emp for emp, info in asignaciones.items() if info['total_piezas'] > piezas_por_empleado]
    empleados_faltantes = [emp for emp, info in asignaciones.items() if info['total_piezas'] < piezas_por_empleado]

    while empleados_faltantes and empleados_con_exceso:
        empleado_con_menos = empleados_faltantes[0]
        empleado_con_mas = empleados_con_exceso[0]

        diferencia = min(asignaciones[empleado_con_mas]['total_piezas'] - piezas_por_empleado,
                         piezas_por_empleado - asignaciones[empleado_con_menos]['total_piezas'])

        asignaciones[empleado_con_mas]['total_piezas'] -= diferencia
        asignaciones[empleado_con_menos]['total_piezas'] += diferencia

        if asignaciones[empleado_con_menos]['total_piezas'] >= piezas_por_empleado:
            empleados_faltantes.pop(0)
        if asignaciones[empleado_con_mas]['total_piezas'] <= piezas_por_empleado:
            empleados_con_exceso.pop(0)

    return asignaciones, directores

# Calcular la carga total que debería tener cada empleado
num_empleados = len(trabajadores)
total_legos = df['Total Piezas'].sum()

# Llamada a la función para distribuir el trabajo y luego redistribuir equitativamente
st.session_state.empleados_asignados, st.session_state.directores_asignados = asignar_legos(df, directores, trabajadores)
st.session_state.asignacion_realizada = True

# Mostrar los scorecards por figura
for pieza in distinct_piezas:
    group = df[df['Nombre'] == pieza]
    empresa = group['Empresa'].iloc[0]
    industria = group['Industria'].iloc[0]
    manual = group['Manual'].iloc[0]
    total_piezas_pieza = group['Total Piezas'].sum()
    director = directores.get(empresa, {}).get('nombre_director', 'Director no disponible')

    # Datos adicionales del scorecard
    legos_distintos_pieza = group['Número de Piezas Distintas'].sum()
    dependencia = group['Dependencia'].iloc[0]
    num_pasos_pieza = group['Paso'].count()
    fecha_inicio = group['Terminado'].iloc[0].strftime("%Y-%m-%d")

    # Obtener los empleados y cuántas piezas están armando para esta figura
    empleados_de_empresa = [
        (empleado, info['figuras'].get(pieza, 0))
        for empleado, info in st.session_state.empleados_asignados.items()
        if pieza in info['figuras'] and info['figuras'][pieza] > 0  # Solo mostrar empleados con piezas asignadas
    ]

    # Crear la lista de empleados con piezas asignadas
    empleados_lista = "<ul>"
    for empleado, piezas in empleados_de_empresa:
        empleados_lista += f"<li>{empleado} ({piezas} piezas)</li>"
    empleados_lista += "</ul>"

    # Insertar el contenido en la tarjeta de scorecard
    table_scorecard += f"""
        <div class="card">   
            <div class="content {header_bg(str(pieza))}">
                <div class="header smallheader">Empresa: {empresa}</div>
                <div class="meta smallheader">Industria: {industria}</div>
            </div>
            <div class="content">
                <div class="description"><br>
                    <div class="column kpi number">{pieza}<br>
                        <p class="kpi text">Total Piezas: {total_piezas_pieza}</p>
                    </div>
                </div>
            </div>
            <div class="extra content">
                <div class="meta"><i class="table icon"></i> Manual: {manual}</div>
                <div class="meta"><i class="user icon"></i> Director: {director}</div>
            </div>
            <div class="extra content" {view_details}> 
                <div class="meta"><i class="edit icon"></i> Piezas Distintas: {legos_distintos_pieza}</div>
                <div class="meta"><i class="folder icon"></i> Número de Pasos: {num_pasos_pieza}</div>
                <div class="meta"><i class="calendar alternate outline icon"></i> Fecha Inicio: {fecha_inicio}</div>
                <div class="meta"><i class="comment alternate outline icon"></i> Manual Dependencia: {dependencia}</div>
            </div>
            <div class="extra content">
                <div class="meta"><i class="users icon"></i> Empleados:
                    {empleados_lista}
                </div>
            </div>
        </div>"""

st.markdown(table_scorecard, unsafe_allow_html=True)
