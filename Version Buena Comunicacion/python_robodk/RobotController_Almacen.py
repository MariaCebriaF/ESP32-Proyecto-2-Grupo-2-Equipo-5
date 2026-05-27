import json


def handle_message(mqtt_client, topic, mensaje, RDK, status_topic):
    print(f"--> Nuevo mensaje en {topic}: {mensaje}")

    try:
        payload = json.loads(mensaje)
    except json.JSONDecodeError:
        print("Error: el mensaje de almacen no es JSON.")
        return

    tipo_id = _int_or_zero(payload.get("tipo_id") or payload.get("id_tipo"))
    tipo = str(payload.get("tipo") or payload.get("nombre") or "").strip()
    posicion = str(payload.get("posicion") or payload.get("pos") or "").strip()
    id_evento = payload.get("id_evento")

    if tipo_id == 0 and not tipo:
        _publish_status(mqtt_client, status_topic, id_evento, "error", "Falta tipo_id/tipo")
        return

    RDK.setParam("almacen_tipo_id", tipo_id)
    RDK.setParam("almacen_tipo", tipo)
    RDK.setParam("almacen_posicion", posicion)
    RDK.setParam("almacen_resultado", "")

    programa = _find_program(RDK, "ProgramaClasificacion")
    if not programa.Valid():
        visibles = _visible_programs(RDK)
        mensaje_error = "No se encontro ProgramaClasificacion"
        if visibles:
            mensaje_error += ". Programas visibles: " + ", ".join(visibles)
        print("Error:", mensaje_error)
        _publish_status(mqtt_client, status_topic, id_evento, "error_robot", mensaje_error)
        return

    result = programa.RunProgram()
    if result == 0:
        _publish_status(mqtt_client, status_topic, id_evento, "error_robot", "RoboDK rechazo iniciar ProgramaClasificacion")
        return

    _publish_status(
        mqtt_client,
        status_topic,
        id_evento,
        "clasificando",
        f"RoboDK inicio {programa.Name()} para tipo_id={tipo_id} posicion={posicion}",
    )


def _find_program(RDK, name):
    candidates = [name, f"{name}.py"] if not name.endswith(".py") else [name, name[:-3]]
    for candidate in candidates:
        item = RDK.Item(candidate)
        if item.Valid():
            return item
    return RDK.Item(name)


def _visible_programs(RDK):
    names = []
    for item in RDK.ItemList():
        try:
            if "programa" in item.Name().lower() or item.Name().endswith(".py"):
                names.append(item.Name())
        except Exception:
            pass
    return names


def _publish_status(mqtt_client, topic, id_evento, estado, mensaje):
    payload = {
        "id_evento": id_evento,
        "estado": estado,
        "mensaje": mensaje,
        "origen": "robodk",
    }
    mqtt_client.publish(topic, json.dumps(payload, ensure_ascii=True))
    print("Publicado estado:", payload)


def _int_or_zero(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

