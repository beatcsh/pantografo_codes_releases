from shapely.geometry import Polygon, JOIN_STYLE, Point
from shapely.ops import unary_union                                    
from typing import List, Tuple                                                  # Importar el módulo csv para poder usar los archivos .csv para las tablas
from ezdxf.math import BSpline
from math import sqrt 
from datetime import datetime                          
import ezdxf                                                #Libreria para convertit de dxf a codigo G
import math
import os     
import re
import numpy as np

uso = 0                                                     #0 Para corte láser, 1 para dremel
of = 0
PULSES_POR_MM = 1                                           #Cuando se requiera obtener el valor en pulsos, se cambia esta variable 
offset = 10                                                #Valor compensación de la herramienta

def punto_medio_arco(inicio, fin, centro, sentido):
    x1, y1 = inicio
    x2, y2 = fin
    cx, cy = centro

    ang_inicio = math.atan2(x1 - cx, y1 - cy)
    ang_fin = math.atan2(x2 - cx, y2 - cy)


    if ang_fin < ang_inicio:
        ang_fin += 2 * math.pi


    ang_medio = (ang_inicio + ang_fin) / 2
    radio = sqrt((x1 - cx)**2 +(y1 - cy)**2)


    if ((x2- x1)*(y2 -y1) > 0) and sentido == 'G3' :
        xm = cx - radio * math.cos(ang_medio)
        ym = cy - radio * math.sin(ang_medio)
    elif (x2- x1)*(y2 -y1) < 0 and sentido == 'G3' : 
        xm = cx + radio * math.cos(ang_medio)
        ym = cy + radio * math.sin(ang_medio)
    elif (x2- x1)*(y2 -y1) < 0 and sentido == 'G2' : 
        xm = cx - radio * math.cos(ang_medio)
        ym = cy - radio * math.sin(ang_medio)
    elif (x2- x1)*(y2 -y1) > 0 and sentido == 'G2' : 
        xm = cx + radio * math.cos(ang_medio)
        ym = cy + radio * math.sin(ang_medio)

    return (xm, ym)

def get_area(points):
    area = 0
    n = len(points)
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        area += (x1 * y2) - (x2 * y1)
    return area / 2 

def get_centroid(points):
    polygon = Polygon(points)
    centroide = polygon.centroid
    return (centroide.x, centroide.y)


def linear_lead_in(points, kerf, uso, is_exterior, tolerance=4):
    if uso == 0:
        def is_closed(contour):
            x0, y0 = contour[0]
            x1, y1 = contour[-1]
            return abs(x0 - x1) < tolerance and abs(y0 - y1) < tolerance

        if not is_exterior and not is_closed(points):
            return [points[0], points[0]]                                   # Sin desplazamiento

        x0, y0 = points[0]

        if not is_exterior:                                                 # Lead-in desde el centroide hasta el primer punto (interior)
            centroid = get_centroid(points)
            return [centroid, (x0, y0)]
        else:                                                             # Lead-in perpendicular al primer segmento (exterior)
            x1, y1 = points[1]
            dx = x1 - x0
            dy = y1 + y0

            angle = math.atan2(dy, dx)
            angle_perp = angle + math.radians(90)

            lead_len = kerf + offset
            lead_dx = -lead_len * math.cos(angle_perp)
            lead_dy = -lead_len * math.sin(angle_perp)

            lead_start = (x0 + lead_dx, y0 + lead_dy)
    else:
        lead_start = points[0]
    return [lead_start] 


def connect_polylines_with_layers(polylines_with_layers):
    result = []
    unused = polylines_with_layers[:] 

    while unused:
        current, layer, tipo, id = unused.pop(0)
        changed = True
        while changed:
            changed = False
            for i, (other, other_layer, other_tipo, other_id) in enumerate(unused):
                if layer != other_layer:
                    continue
                if points_equal(current[-1], other[0]):
                    current += other[1:]
                    unused.pop(i)
                    changed = True
                    break
                elif points_equal(current[0], other[-1]):
                    current = other[:-1] + current
                    unused.pop(i)
                    changed = True
                    break
                elif points_equal(current[-1], other[-1]):
                    current += list(reversed(other[:-1]))
                    unused.pop(i)
                    changed = True
                    break
                elif points_equal(current[0], other[0]):
                    current = list(reversed(other[1:])) + current
                    unused.pop(i)
                    changed = True
                    break
        result.append((current, layer, tipo, id))

    return result

def fit_circle(xs, ys):
    """Ajusta un círculo por mínimos cuadrados a un conjunto de puntos."""
    A = np.c_[2*xs, 2*ys, np.ones(len(xs))]
    b = xs**2 + ys**2
    c, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
    cx, cy = c[0], c[1]
    r = sqrt(c[2] + cx**2 + cy**2)
    return (cx, cy, r)

def detectar_varios_arcos(puntos, min_puntos=40, max_puntos=43, tolerancia=0.5):

    arcos_encontrados = []
    n = len(puntos)
    i = 0

    while i < n - min_puntos:
        encontrado = False
        for j in range(i + min_puntos, min(i + max_puntos, n)):
            segmento = puntos[i:j]
            xs = np.array([p[0] for p in segmento])
            ys = np.array([p[1] for p in segmento])

            try:
                cx, cy, r = fit_circle(xs, ys)
            except np.linalg.LinAlgError:
                continue

            # Error promedio del ajuste
            errores = [abs(sqrt((x - cx)**2 + (y - cy)**2) - r) for x, y in zip(xs, ys)]
            error_prom = np.mean(errores)

            if error_prom < tolerancia:
                punto_inicio = puntos[i]
                punto_final = puntos[j - 1]
                centro = (cx- punto_inicio[0], cy-punto_inicio[1])
                arcos_encontrados.append((punto_inicio, punto_final, centro))
                i = j  # Saltamos al final del arco
                encontrado = True
                break

        if not encontrado:
            i += 1

    return arcos_encontrados

def points_equal(p1, p2, eps=1e-6):
    return abs(p1[0] - p2[0]) < eps and abs(p1[1] - p2[1]) < eps

def extract_entities_as_segments(msp):
    segments = []
    texts = []
    circles = []  # Cambia de una sola variable a una lista

    for entity in msp:
        points = []

        if entity.dxftype() == 'LINE':
            start = (entity.dxf.start.x, entity.dxf.start.y)
            end = (entity.dxf.end.x, entity.dxf.end.y)
            points = [start, end]

        elif entity.dxftype() == 'ARC':
            center = (entity.dxf.center.x, entity.dxf.center.y)
            r = entity.dxf.radius
            start_a = math.radians(entity.dxf.start_angle)
            end_a = math.radians(entity.dxf.end_angle)
            if end_a < start_a:
                end_a += 2 * math.pi
            steps = 40
            arc_points = [
                (center[0] + r * math.cos(start_a + j * (end_a - start_a) / steps),
                 center[1] + r * math.sin(start_a + j * (end_a - start_a) / steps))
                for j in range(steps + 1)
            ]
            points = arc_points
            # arc_id = len(arcs)  # El índice que tendrá en circles
            # arcs.append({'points': arc_points, 'center': center, 'radius': r, 'start_angle': entity.dxf.start_angle, 'end_angle': entity.dxf.end_angle, 'layer': entity.dxf.layer})
            # segments.append((points, entity.dxf.layer, 'arc', arc_id))

        elif entity.dxftype() == 'CIRCLE':
            center = (entity.dxf.center.x, entity.dxf.center.y)
            r = entity.dxf.radius
            steps = 40
            circle_points = [
                (center[0] + r * math.cos(2 * math.pi * j / steps),
                center[1] + r * math.sin(2 * math.pi * j / steps))
                for j in range(steps + 1)
            ]
            points = circle_points
            circle_id = len(circles)  # El índice que tendrá en circles
            circles.append({'points': circle_points, 'center': center, 'radius': r, 'layer': entity.dxf.layer})
            segments.append((points, entity.dxf.layer, 'circle', circle_id))


        elif entity.dxftype() == 'ELLIPSE':
            center = (entity.dxf.center.x, entity.dxf.center.y)
            major_axis = entity.dxf.major_axis
            ratio = entity.dxf.ratio
            start_param = entity.dxf.start_param
            end_param = entity.dxf.end_param
            steps = 40
            a = math.hypot(*major_axis[:2])
            angle = math.atan2(major_axis[1], major_axis[0])
            b = a * ratio
            points = [
                (
                    center[0] + a * math.cos(t) * math.cos(angle) - b * math.sin(t) * math.sin(angle),
                    center[1] + a * math.cos(t) * math.sin(angle) + b * math.sin(t) * math.cos(angle)
                )
                for t in [start_param + i * (end_param - start_param) / steps for i in range(steps + 1)]
            ]

        elif entity.dxftype() == 'SPLINE':
            spline = entity.construction_tool()
            points = [(p.x, p.y) for p in spline.approximate(segments=50)]

        elif entity.dxftype() == 'LWPOLYLINE':
            points = [(pt[0], pt[1]) for pt in entity.get_points()]
            # if entity.closed:
            #     points.append(points[0])

        elif entity.dxftype() == 'POLYLINE':
            points = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]

        elif entity.dxftype() == 'HATCH':
            for path in entity.paths:
                if path.PATH_TYPE_EDGE:
                    poly = []
                    for edge in path.edges:
                        if edge.type == 'LineEdge':
                            poly.append((edge.start[0], edge.start[1]))
                            poly.append((edge.end[0], edge.end[1]))
                        elif edge.type == 'ArcEdge':
                            center = edge.center
                            r = edge.radius
                            start_a = math.radians(edge.start_angle)
                            end_a = math.radians(edge.end_angle)
                            if edge.is_counter_clockwise:
                                if end_a < start_a:
                                    end_a += 2 * math.pi
                            else:
                                if start_a < end_a:
                                    start_a += 2 * math.pi
                                start_a, end_a = end_a, start_a
                            steps = 20
                            arc_points = [
                                (
                                    center[0] + r * math.cos(start_a + j * (end_a - start_a) / steps),
                                    center[1] + r * math.sin(start_a + j * (end_a - start_a) / steps)
                                )
                                for j in range(steps + 1)
                            ]
                            poly.extend(arc_points)
                    if poly:
                        segments.append(poly)
                    continue
        elif entity.dxftype() in ('TEXT', 'MTEXT'):
            try:
                insert = entity.dxf.insert if entity.dxftype() == 'TEXT' else entity.dxf.insert
                content = entity.text if entity.dxftype() == 'TEXT' else entity.plain_text()
                texts.append({
                    'position': (insert.x, insert.y),
                    'text': content.strip(),
                    'rotation': getattr(entity.dxf, 'rotation', 0),
                    'height': getattr(entity.dxf, 'height', 1),
                })
            except Exception as e:
                print(f"Error leyendo texto: {e}")
        
        else:
            print("No se encontró una figura")

        if points:
            segments.append((points, entity.dxf.layer, None, None))

    return segments, circles #, arcs


def generate_gcode_from_dxf(filename, z_value, kerf, uso, zp, pa, of):                      #Empieza a crear el código G
    doc = ezdxf.readfile(filename)                          #Lee el archivo .dxf con ezdxf
    msp = doc.modelspace()                                  #Crea un modelo en el espacio para ser utilizado
    gcode = []    
    circles_id = []
    def code_impr(corte_por_pasada,  circles, tipo, id):    #circles, arcs
        arcos = detectar_varios_arcos(ord)
        
        gcode.append(f"( {kind} corte )")
        gcode.append(f"G0 X{lead[0][0]:.3f} Y{lead[0][1]:.3f} Z{z_value +10:.3f}")                            
        gcode.append(f"G0 X{lead[0][0]:.3f} Y{lead[0][1]:.3f} Z{z_value - corte_por_pasada:.3f}")
        gcode.append("M03 ; plasma ON")
        # Detectar si ord es un círculo
        if kind == 'Exterior':
            kind_kerf = kerf
        elif kind == 'Interior':
            kind_kerf = -kerf

        if tipo == 'circle':
            center = circles[id]['center']
            r = circles[id]['radius']
            # Puedes ajustar el Z y otros parámetros según tu lógica
            gcode.append(f"G1 X{center[0]+r+kind_kerf:.3f} Y{center[1]:.3f} Z{z_value - corte_por_pasada:.3f}")
            gcode.append(f"(Circulo)")
            gcode.append(f"(Circulo numero {id})")
            gcode.append(f"G2 X{center[0]+r+kind_kerf:.3f} Y{center[1]:.3f} I{-r-kind_kerf:.3f} J0 Z{z_value - corte_por_pasada:.3f}")
            gcode.append("M05 ; plasma OFF")
            gcode.append(f"G0 X{center[0]+r+kind_kerf:.3f} Y{center[1]:.3f} Z{z_value + 10:.3f}")

        else:
            i = 0
            while i < len(ord):
                pt = ord[i]
                arco_encontrado = False

                for inicio, fin, centro in arcos:
                    if pt == inicio:
                        gcode.append(f"G1 X{inicio[0]:.3f} Y{inicio[1]:.3f} Z{z_value - corte_por_pasada:.3f}")
                        area_arc = get_area(ord)

                        if area_arc > 0:
                            gcode.append(f"(Arco G3)")
                            gcode.append(f"G3 X{fin[0]:.3f} Y{fin[1]:.3f} I{centro[0]:.3f} J{centro[1]:.3f} Z{z_value - corte_por_pasada:.3f}")
                        else:
                            gcode.append(f"(Arco G2)")
                            gcode.append(f"G2 X{fin[0]:.3f} Y{fin[1]:.3f} I{centro[0]:.3f} J{centro[1]:.3f} Z{z_value - corte_por_pasada:.3f}")
                        i += 40  # Saltar los siguientes 40 puntos
                        arco_encontrado = True
                        break

                if not arco_encontrado:
                    gcode.append(f"G1 X{pt[0]:.3f} Y{pt[1]:.3f} Z{z_value - corte_por_pasada:.3f}")
                    i += 1

            # Finalización del corte
            gcode.append("M05 ; plasma OFF")
            gcode.append(f"G0 X{pt[0]:.3f} Y{pt[1]:.3f} Z{z_value +10:.3f}")


    gcode.append("G21 ; mm")                                #Declara que las unidades son milimetros
    gcode.append("G90 ; abs")                               #Las coordenadas serán absolutas
    gcode.append("M05 ; plasma off")                        #Inicia el programa con el cortador de plasma desenergizado

    acc_data, circles = extract_entities_as_segments(msp)   #arcs
    orden_capas = connect_polylines_with_layers(acc_data)


    capas_detectadas = set()
    for entity in msp:
        if hasattr(entity.dxf, "layer"):
            capas_detectadas.add(entity.dxf.layer)
    
    if len(capas_detectadas) > 1:
        # Filtrar fuera la capa "0"
        orden_capas = [(poly, layer) for poly, layer in orden_capas if layer != "0"]
    areas = [(get_area(polygon), polygon, layer, tipo, id) for polygon, layer, tipo, id in orden_capas]
    areas.sort(key=lambda x: abs(x[0]), reverse=True)


    clasificados = []
    for idx, (area, polygon, layer, tipo, id) in enumerate(areas):
        is_outer = idx == 0
        clasificados.append((polygon, is_outer, layer, tipo, id))  # Añadir tipo y circle_id a la tupla

    # Separar interiores y exteriores
    interiores = [item for item in clasificados if not item[1]]
    exteriores = [item for item in clasificados if item[1]]
    orden_dibujo = interiores + exteriores
    save = zp

    if uso == 0:
        pa = 1
        zp = 0
    for n in range(1, pa+1):
        gcode.append(f"Pasada: {n}")
        for ord, is_outer, capa_actual, tipo, id in orden_dibujo:
            kind = 'Exterior' if is_outer else 'Interior'
            if (of == 0) and ((capa_actual == "LAYER0") or (len(capas_detectadas)==1)):
                circles_id.append(id)                                                                 # Verificar si el contorno está cerrado antes de crear el polígono
                if len(ord) > 2 and (ord[0][0] == ord[-1][0] and ord[0][1] == ord[-1][1]):
                    poly = Polygon(ord)                                                         # Solo crear el polígono si está cerrado
                    offset = kerf if is_outer else -kerf
                    buffered = poly.buffer(offset, join_style=JOIN_STYLE.mitre)

                    if not buffered.is_empty and buffered.geom_type == 'Polygon':
                        ord = list(buffered.exterior.coords)
                    else:                                                                        # Si hay error en el buffer, saltar figura
                        print("Ocurrió un error con el offset")
                                                                            # Si la figura no está cerrada, no aplicar offset ni crear polígono
                          

            if (capa_actual == "LAYER1") and (len(capas_detectadas)>1):
                zp = 0.1
            else:
                zp = save
                
            if len(capas_detectadas) > 1:
                if capa_actual == "0":
                    # No hacer nada si hay más de una capa y esta es la capa 0
                    continue
                elif capa_actual != "0":
                    lead = linear_lead_in(ord, kerf, uso, is_exterior=is_outer)
                    corte_por_pasada = n*zp/pa
                    code_impr(corte_por_pasada,  circles, tipo, id)         #circles, arcs
                    
            elif len(capas_detectadas)==1:
                lead = linear_lead_in(ord, kerf, uso, is_exterior=is_outer)
                corte_por_pasada = n*zp/pa
                code_impr(corte_por_pasada, circles, tipo, id)              #circles, arcs
   
    gcode.append("M30 ; fin")                                                       #Finaliza el programa
    return [str(line) for line in gcode]

predet = 25                                                                     #Valores predeterminados de velocidad VJ
velocidades = predet

def gcode_a_yaskawa(gcode_lines, z_altura, velocidad, nombre_base, output_dir, uf, ut, pc, velocidadj, zp, circles, circles_id, kerf, aspeed):     #Traducción del codigo G a inform 2
    nombre, extension = os.path.splitext(nombre_base)                   # Separar nombre y extensión
    nombre_limpio = re.sub(r'[^a-zA-Z0-9]', '', nombre)                 # Limpiar: quitar todo lo que no sea letras o números
    nombre_limpio = nombre_limpio[:9]                                   # Recortar a máximo 6 caracteres
    nuevo_nombre = f"{nombre_limpio}{extension}"                        # Crear nuevo nombre completo                                        

    jbi_path = os.path.join(output_dir, f"{nuevo_nombre}.JBI")                #Dirección y tipo de archivo del programa inform 2 (del robot)
    g_path = os.path.join(output_dir, f"{nuevo_nombre}.gcode")                #Dirección y tipo de archivo del código G
    aum = 0
    try:
        with open(g_path, "w") as gf:                                           #Abre el archivo del código G para empezar a traducirlo
            gf.write("".join(map(str, gcode_lines)))

        with open(jbi_path, "w") as f:                                                  #Abre el archivo del inform 2 para empezar a escribir
            f.write("/JOB\n")                                                           #Indica tipo de archivo
            f.write(f"//NAME {nuevo_nombre.upper()}\n")                               #Nombre del JOB
            f.write("//POS\n")                                                          #Indica posiciones
            total_pos = sum(1 for line in gcode_lines if line.startswith("G")) + sum(4 for line in gcode_lines if line.startswith("(Circulo)")) + sum(2 for line in gcode_lines if line.startswith("(Arco G2)")) + sum(2 for line in gcode_lines if line.startswith("(Arco G3)"))       #Determina el número total de posiciones
            f.write(f"///NPOS {total_pos},0,0,0,0,0\n")                                 #Número total de posiciones
            f.write(f"///TOOL {ut}\n")                                                  #Número de herramienta
            f.write(f"///USER {uf}\n")                                                  #Número de usuario
            f.write("///POSTYPE USER\n")                                                #Indica el tipo de movimiento (Usuario en este caso)
            f.write("///RECTAN \n")                                                     #Indica las unidades (milimetros en este caso)
            f.write("///RCONF 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0\n")       #Configuraciones del robot (Por investigar a fondo)
            idx = 0                                                     
            posiciones = []                                         
            for i, line in enumerate(gcode_lines):                                      #Genera las coordenadas y su número correspondiente
                if (line.startswith("G0") or line.startswith("G1")):                      #Identifica si es G0 o G1
                    parts = line.split()
                    coords = {p[0]: float(p[1:]) for p in parts[1:] if p[0] in "XYZ"}
                    x = round(coords.get("X", 0.0), 4)                                  #Redondea los valores a cuatro decimales
                    y = round(coords.get("Y", 0.0), 4)
                    z = round(coords.get("Z", 0.0), 4)
                    posiciones.append((x, y, z))
                    f.write(f"C{idx:05d}={x},{y},{z},0,0,0\n")                          #Escribe los valores acomodados
                    idx += 1
                elif line.startswith("G2 ") or line.startswith("G3 "):
                    parts = line.split()
                    coords = {p[0]: float(p[1:]) for p in parts[1:] if p[0] in "XYIJZ"}
                    x = round(coords.get("X", 0.0), 4)                                  #Redondea los valores a cuatro decimales
                    y = round(coords.get("Y", 0.0), 4)
                    xi = round(coords.get("I", 0.0), 4)
                    yj = round(coords.get("J", 0.0), 4)
                    z = round(coords.get("Z", 0.0), 4)
                    ax, ay, az = posiciones[-1]
                    centro = (ax + xi), (ay + yj)
                    if ax == x and ay == y and gcode_lines[i - 2].startswith("(Circulo)"):  
                        cuad_1 = (round(x + xi, 2), round(y - xi, 2))
                        cuad_2 = (round(x + 2*xi, 2), round(y, 2))
                        cuad_3 = (round(x + xi, 2), round(y + xi, 2))
                        f.write(f"C{idx:05d}={ax},{ay},{z},0,0,0\n")
                        f.write(f"C{idx+1:05d}={cuad_1[0]},{cuad_1[1]},{z},0,0,0\n") 
                        f.write(f"C{idx+2:05d}={cuad_2[0]},{cuad_2[1]},{z},0,0,0\n")
                        f.write(f"C{idx+3:05d}={cuad_3[0]},{cuad_3[1]},{z},0,0,0\n") 
                        f.write(f"C{idx+4:05d}={ax},{ay},{z},0,0,0\n")
                        idx += 5
                    else:
                        inicio = ax, ay                                                 #Si es un arco
                        final = x, y
                        arco = inicio, centro, final
                        area_arc = get_area(arco)
                        if area_arc < 0 : sentido = 'G2'  
                        else: sentido = 'G3'
                        pmx, pmy = punto_medio_arco(inicio, final, centro, sentido)    # ya se redondean abajo
                        pmx = round(float(pmx), 3)
                        pmy = round(float(pmy), 3)
                        posiciones.append((x, y, xi, yj,z))
                        f.write(f"C{idx:05d}={ax},{ay},{z},0,0,0\n")
                        f.write(f"C{idx+1:05d}={pmx},{pmy},{z},0,0,0\n")             
                        f.write(f"C{idx+2:05d}={x},{y},{z},0,0,0\n")       
                        idx += 3
            
            f.write("///POSTYPE PULSE\n")
            f.write("///PULSE\n")
            f.write(f"C{idx:05d}=0,0,0,0,0,0\n") 
            f.write(f"C{idx +1:05d}=0,0,0,0,0,0\n")  

            f.write("//INST\n")                                                         #Instrucciones
            f.write(f"///DATE {datetime.now().strftime('%Y/%m/%d %H:%M')}\n")           #Fecha
            f.write("///ATTR SC,RW,RJ\n")                                               #Shared constant, read/write y Relative Job
            f.write(f"////FRAME USER {uf}\n")                                               #User frame 1
            f.write("///GROUP1 RB1\n")                                                  #Grupo de coordenadas
            f.write("NOP\n")
            f.write(f"DOUT OT#({pc}) OFF\n")                                            #Al final del programa, apaga la antorcha
            f.write(f"MOVJ C{idx +1:05d} VJ=10.0\n")
            #Escribe los movimientos, junto con el prendido y apagado de la antorcha y timers
            if velocidades == predet:                                                   
                j = 0
                i = 0
                while i < len(gcode_lines):                                                 
                    line = gcode_lines[i]
                    if line.startswith("G0"):                                           #Si lee un G0, escribe un MOVJ con VJ
                        f.write(f"MOVJ C{j:05d} VJ={velocidadj}\n")
                        j += 1
                    elif line.startswith("G1"):                                         #Si lee un G1, escribe un MOVL con V
                        f.write(f"MOVL C{j:05d} V={velocidad} PL=0\n")
                        j += 1
                    elif line.startswith("M03"):                                        #Si lee un M03, escribe el encendido de la antorcha y 
                        f.write(f"DOUT OT#({pc}) ON\n")                                 #Agrega un pequeño timer de 1 segundo
                        f.write(f"TIMER T=2.00\n")
                    elif line.startswith("M05"):                                        #Si lee un M05, apaga la antorcha con un timer
                        f.write(f"DOUT OT#({pc}) OFF\n")
                        f.write(f"TIMER T=2.00\n")
                    elif line.startswith("G2") or line.startswith("G3"):              #Si lee un G2, escribe un MOVC con V
                        if gcode_lines[i - 2].startswith("(Circulo)"): 
                            f.write(f"MOVC C{j:05d} V={aspeed}\n")
                            f.write(f"MOVC C{j+1:05d} V={aspeed}\n")
                            f.write(f"MOVC C{j+2:05d} V={aspeed} FPT\n")
                            f.write(f"MOVC C{j+3:05d} V={aspeed}\n")
                            f.write(f"MOVC C{j+4:05d} V={aspeed} FPT\n")
                            j += 5
                        elif gcode_lines[i - 1].startswith("(Arco G2)") or gcode_lines[i - 1].startswith("(Arco G3)"):
                            f.write(f"MOVC C{j:05d} V={aspeed}\n")
                            f.write(f"MOVC C{j+1:05d} V={aspeed}\n")
                            f.write(f"MOVC C{j+2:05d} V={aspeed} FPT\n")
                            j += 3

                    else:
                        pass  # No se incrementa j                                      #Si no lee nada, pasa a la siguiente línea
                    i += 1  # Siempre pasa a la siguiente línea

                    
            f.write(f"DOUT OT#({pc}) OFF\n")                                            #Al final del programa, apaga la antorcha
            f.write(f"MOVJ C{j:05d} VJ=10.0\n")
            f.write("END\n")                                                            #Fin del programa

        return jbi_path, g_path 
    except Exception as e:
        raise e