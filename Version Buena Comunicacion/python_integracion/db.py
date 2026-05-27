from __future__ import annotations

import os
import unicodedata
from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg.rows import dict_row


DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/medicamentos"
DEFAULT_PRECIO_VENTA = float(os.getenv("DEFAULT_PRECIO_VENTA", "0"))
DEFAULT_SEGURO_SS = os.getenv("DEFAULT_SEGURO_SS", "false").lower() in {"1", "true", "yes", "si"}

MEDICINE_ALIASES = {
    "paracetamol": "Paracetamol",
    "ibuprofeno": "Ibuprofeno",
    "enantyum": "Enantyum",
    # En versiones anteriores del demo el tercer medicamento se registraba con este nombre,
    # pero la ESP32 de pedido, la web y RoboDK trabajan con Enantyum.
    "amoxicilina": "Enantyum",
}

MEDICINE_NAMES_BY_ID = {
    1: "Paracetamol",
    2: "Ibuprofeno",
    3: "Enantyum",
}


@dataclass(frozen=True)
class Reservation:
    ok: bool
    estado: str
    mensaje: str
    id_pedido: str | None = None
    id_medicamento: str | None = None
    tipo_id: int | None = None
    tipo: str | None = None
    cantidad: int = 0
    posicion: str | None = None
    cod_barras: str | None = None
    caducidad: str | None = None
    precio_total: float | None = None


def database_url(value: str | None = None) -> str:
    return value or os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def connect(db_url: str | None = None) -> psycopg.Connection:
    return psycopg.connect(database_url(db_url), row_factory=dict_row)


def validate_schema(db_url: str | None = None) -> None:
    required_tables = {
        "medicamento",
        "cliente",
        "venta",
        "caja_grande",
        "cinta_transportadora",
        "sensor",
        "robot",
        "herramienta",
        "contiene",
    }
    with connect(db_url) as conn:
        rows = conn.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            """
        ).fetchall()

    found = {row["table_name"] for row in rows}
    missing = sorted(required_tables - found)
    if missing:
        raise RuntimeError(f"Faltan tablas en PostgreSQL: {', '.join(missing)}")


def seed_demo_data(db_url: str | None = None) -> None:
    rows = [
        ("MED001", 847000100001, "Paracetamol", "2027-05-01", "Demo", 3, "disponible", "X01-Y01", 3.50, True),
        ("MED002", 847000100002, "Ibuprofeno", "2027-08-15", "Demo", 2, "disponible", "X01-Y02", 4.10, True),
        ("MED003", 847000100003, "Enantyum", "2026-11-20", "Demo", 1, "disponible", "X02-Y01", 6.25, True),
    ]
    with connect(db_url) as conn:
        for row in rows:
            existing = conn.execute(
                """
                SELECT id_medicamento
                FROM medicamento
                WHERE cod_barras::text = %s
                LIMIT 1
                """,
                (str(row[1]),),
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE medicamento
                    SET nombre = %s,
                        caducidad = %s,
                        descripcion = %s,
                        stock = %s,
                        estado = %s,
                        pos = %s,
                        precio_venta = %s,
                        seguro_ss = %s
                    WHERE id_medicamento = %s
                    """,
                    (row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], existing["id_medicamento"]),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO medicamento (
                      id_medicamento, cod_barras, nombre, caducidad, descripcion,
                      stock, estado, pos, precio_venta, seguro_ss
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id_medicamento) DO UPDATE SET
                      cod_barras = EXCLUDED.cod_barras,
                      nombre = EXCLUDED.nombre,
                      caducidad = EXCLUDED.caducidad,
                      descripcion = EXCLUDED.descripcion,
                      stock = EXCLUDED.stock,
                      estado = EXCLUDED.estado,
                      pos = EXCLUDED.pos,
                      precio_venta = EXCLUDED.precio_venta,
                      seguro_ss = EXCLUDED.seguro_ss
                    """,
                    row,
                )


def register_storage_event(payload: dict[str, Any], db_url: str | None = None) -> bool:
    tipo_id = medicine_id_from_payload(payload)
    nombre = normalize_medicine_name(payload.get("nombre") or payload.get("tipo") or medicine_name_from_id(tipo_id))
    posicion = str(payload.get("pos") or payload.get("posicion") or "").strip()
    cantidad = int(payload.get("cantidad") or 1)
    cod_barras = _barcode_or_empty(payload.get("cod_barras"))
    caducidad = payload.get("caducidad")

    if not nombre or not posicion:
        raise ValueError("El evento de almacen necesita nombre/tipo y pos/posicion")
    if not caducidad:
        raise ValueError("El evento de almacen necesita caducidad")
    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor que cero")

    with connect(db_url) as conn:
        with conn.transaction():
            existing = _find_medicine_for_update(conn, nombre, cod_barras)
            if existing:
                conn.execute(
                    """
                    UPDATE medicamento
                    SET stock = stock + %s,
                        nombre = %s,
                        estado = 'disponible',
                        pos = COALESCE(%s, pos),
                        caducidad = COALESCE(%s, caducidad),
                        cod_barras = COALESCE(NULLIF(%s, ''), cod_barras)
                    WHERE id_medicamento = %s
                    """,
                    (cantidad, nombre, posicion, caducidad, cod_barras, existing["id_medicamento"]),
                )
                return False

            id_medicamento = str(
                payload.get("id_medicamento")
                or payload.get("id_evento")
                or (f"MED{cod_barras}" if cod_barras else f"MED{nombre[:8].upper()}")
            ).strip()
            conn.execute(
                """
                INSERT INTO medicamento (
                  id_medicamento, cod_barras, nombre, caducidad, descripcion,
                  stock, estado, pos, precio_venta, seguro_ss
                )
                VALUES (%s, %s, %s, %s, %s, %s, 'disponible', %s, %s, %s)
                """,
                (
                    id_medicamento,
                    cod_barras,
                    nombre,
                    caducidad,
                    payload.get("descripcion"),
                    cantidad,
                    posicion,
                    float(payload.get("precio_venta") or DEFAULT_PRECIO_VENTA),
                    bool(payload.get("seguro_SS", payload.get("seguro_ss", DEFAULT_SEGURO_SS))),
                ),
            )
            return True


def reserve_order(payload: dict[str, Any], db_url: str | None = None) -> Reservation:
    id_pedido = str(payload.get("id_pedido") or "").strip()
    tipo_id = medicine_id_from_payload(payload)
    nombre = normalize_medicine_name(payload.get("nombre") or payload.get("tipo") or medicine_name_from_id(tipo_id))
    cantidad = int(payload.get("cantidad") or 1)
    dni = payload.get("DNI") or payload.get("dni")

    if not id_pedido:
        raise ValueError("El pedido necesita id_pedido")
    if not nombre:
        raise ValueError("El pedido necesita nombre/tipo")
    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor que cero")

    with connect(db_url) as conn:
        with conn.transaction():
            lookup_terms = _medicine_lookup_terms(nombre)
            item = conn.execute(
                """
                SELECT *
                FROM medicamento
                WHERE lower(trim(nombre)) = ANY(%s::text[])
                  AND stock >= %s
                  AND lower(trim(estado)) IN ('disponible', 'ok', 'activo')
                ORDER BY caducidad ASC, id_medicamento ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
                """,
                (lookup_terms, cantidad),
            ).fetchone()

            if not item:
                return Reservation(False, "no_disponible", "No hay stock disponible", id_pedido, tipo_id=tipo_id, tipo=nombre, cantidad=cantidad)

            new_stock = int(item["stock"]) - cantidad
            new_state = "disponible" if new_stock > 0 else "agotado"
            conn.execute(
                """
                UPDATE medicamento
                SET stock = %s, estado = %s, nombre = %s
                WHERE id_medicamento = %s
                """,
                (new_stock, new_state, nombre, item["id_medicamento"]),
            )

            precio_total = float(item["precio_venta"]) * cantidad
            if dni:
                conn.execute(
                    """
                    INSERT INTO venta (dni, id_medicamento, fecha_venta, precio_total)
                    VALUES (%s, %s, CURRENT_DATE, %s)
                    ON CONFLICT (dni, id_medicamento, fecha_venta) DO UPDATE SET
                      precio_total = venta.precio_total + EXCLUDED.precio_total
                    """,
                    (dni, item["id_medicamento"], precio_total),
                )

            return Reservation(
                True,
                "reservado",
                "Stock reservado; pendiente de RoboDK",
                id_pedido=id_pedido,
                id_medicamento=item["id_medicamento"],
                tipo_id=tipo_id,
                tipo=nombre,
                cantidad=cantidad,
                posicion=str(item["pos"]).strip() if item["pos"] is not None else None,
                cod_barras=str(item["cod_barras"]),
                caducidad=str(item["caducidad"]),
                precio_total=precio_total,
            )


def update_order_status(
    _id_pedido: str,
    _estado: str,
    _mensaje: str,
    _db_url: str | None = None,
) -> None:
    # Vuestro esquema no tiene tabla Pedido. El estado del flujo se comunica por MQTT.
    return None


def inventory_snapshot(db_url: str | None = None) -> list[dict[str, Any]]:
    with connect(db_url) as conn:
        rows = conn.execute(
            """
            SELECT id_medicamento, cod_barras, nombre, caducidad, stock, estado, pos, precio_venta, seguro_ss
            FROM medicamento
            ORDER BY pos ASC NULLS LAST, nombre ASC
            """
        ).fetchall()
        return [dict(row) for row in rows]


def _find_medicine_for_update(conn: psycopg.Connection, nombre: str, cod_barras: str) -> dict[str, Any] | None:
    if cod_barras:
        row = conn.execute(
            """
            SELECT *
            FROM medicamento
            WHERE cod_barras::text = %s
            LIMIT 1
            FOR UPDATE
            """,
            (cod_barras,),
        ).fetchone()
        if row:
            return row

    return conn.execute(
        """
        SELECT *
        FROM medicamento
        WHERE lower(trim(nombre)) = ANY(%s::text[])
        LIMIT 1
        FOR UPDATE
        """,
        (_medicine_lookup_terms(nombre),),
    ).fetchone()


def normalize_medicine_name(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""

    key = _medicine_key(raw)
    return MEDICINE_ALIASES.get(key, raw)


def medicine_id_from_payload(payload: dict[str, Any]) -> int | None:
    for field in ("tipo_id", "id_tipo", "medicine_id", "id_medicamento"):
        value = payload.get(field)
        try:
            medicine_id = int(value)
        except (TypeError, ValueError):
            continue
        if medicine_id in MEDICINE_NAMES_BY_ID:
            return medicine_id
    return None


def medicine_name_from_id(medicine_id: int | None) -> str:
    if medicine_id is None:
        return ""
    return MEDICINE_NAMES_BY_ID.get(medicine_id, "")


def _medicine_lookup_terms(nombre: str) -> list[str]:
    canonical = normalize_medicine_name(nombre)
    canonical_key = _medicine_key(canonical)
    terms = {canonical.lower()}
    for alias, target in MEDICINE_ALIASES.items():
        if _medicine_key(target) == canonical_key:
            terms.add(alias)
    return sorted(terms)


def _medicine_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).strip().lower()


def _barcode_or_empty(value: Any) -> str:
    return str(value or "").strip()
