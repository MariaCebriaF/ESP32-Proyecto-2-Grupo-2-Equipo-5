from __future__ import annotations

import argparse

from db import database_url, inventory_snapshot, seed_demo_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Inicializa medicamentos de demo en PostgreSQL")
    parser.add_argument("--database-url", default=database_url(), help="URL PostgreSQL")
    args = parser.parse_args()

    seed_demo_data(args.database_url)
    print(f"Base de datos preparada: {args.database_url}")
    for item in inventory_snapshot(args.database_url):
        print(f"- {item['tipo']} {item['posicion']} stock={item['stock']} caducidad={item['caducidad']}")


if __name__ == "__main__":
    main()
