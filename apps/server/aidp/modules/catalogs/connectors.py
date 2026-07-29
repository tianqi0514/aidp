import json
import time
from dataclasses import dataclass
from typing import Any, Protocol

import psycopg


@dataclass(frozen=True)
class DiscoveredResource:
    external_id: str
    name: str
    namespace: str
    category: str
    schema: dict[str, Any]
    row_estimate: int | None = None


class Connector(Protocol):
    def test(self, config: dict[str, Any], secret: str | None) -> dict[str, Any]: ...

    def discover(
        self, config: dict[str, Any], secret: str | None, scope: dict[str, Any]
    ) -> list[DiscoveredResource]: ...


def _credentials(secret: str | None) -> dict[str, str]:
    if not secret:
        return {}
    try:
        value = json.loads(secret)
    except json.JSONDecodeError:
        return {"password": secret}
    if not isinstance(value, dict):
        raise ValueError("Database secret must be a JSON object or password string")
    return {str(key): str(item) for key, item in value.items()}


class PostgreSQLConnector:
    def _connect(self, config: dict[str, Any], secret: str | None):
        credentials = _credentials(secret)
        return psycopg.connect(
            host=config["host"],
            port=int(config.get("port", 5432)),
            dbname=config["database"],
            user=credentials.get("username") or config.get("username"),
            password=credentials.get("password"),
            sslmode=config.get("sslmode", "prefer"),
            connect_timeout=int(config.get("connect_timeout", 10)),
            options="-c default_transaction_read_only=on",
        )

    def test(self, config: dict[str, Any], secret: str | None) -> dict[str, Any]:
        started = time.perf_counter()
        with self._connect(config, secret) as connection, connection.cursor() as cursor:
            cursor.execute("select current_database(), current_user, version()")
            database, user, version = cursor.fetchone()
        return {
            "latency_ms": round((time.perf_counter() - started) * 1000),
            "database": database,
            "user": user,
            "server_version": version,
        }

    def discover(
        self, config: dict[str, Any], secret: str | None, scope: dict[str, Any]
    ) -> list[DiscoveredResource]:
        requested_schemas = scope.get("schemas") or config.get("schemas") or ["public"]
        name_pattern = scope.get("name_pattern") or "%"
        resources: dict[tuple[str, str], dict[str, Any]] = {}
        with self._connect(config, secret) as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                    select table_schema, table_name, table_type
                    from information_schema.tables
                    where table_schema = any(%s) and table_name like %s
                    order by table_schema, table_name
                    """,
                (requested_schemas, name_pattern),
            )
            for namespace, name, table_type in cursor.fetchall():
                resources[(namespace, name)] = {
                    "external_id": f"{config['database']}.{namespace}.{name}",
                    "name": name,
                    "namespace": namespace,
                    "category": "view" if table_type == "VIEW" else "table",
                    "fields": [],
                    "primary_key": [],
                }
            cursor.execute(
                """
                    select table_schema, table_name, column_name, data_type, is_nullable,
                           column_default, ordinal_position, character_maximum_length,
                           numeric_precision, numeric_scale
                    from information_schema.columns
                    where table_schema = any(%s) and table_name like %s
                    order by table_schema, table_name, ordinal_position
                    """,
                (requested_schemas, name_pattern),
            )
            for row in cursor.fetchall():
                namespace, name = row[0], row[1]
                if (namespace, name) not in resources:
                    continue
                resources[(namespace, name)]["fields"].append(
                    {
                        "name": row[2],
                        "type": row[3],
                        "nullable": row[4] == "YES",
                        "default": row[5],
                        "position": row[6],
                        "length": row[7],
                        "precision": row[8],
                        "scale": row[9],
                    }
                )
            cursor.execute(
                """
                    select tc.table_schema, tc.table_name, kcu.column_name
                    from information_schema.table_constraints tc
                    join information_schema.key_column_usage kcu
                      on tc.constraint_name = kcu.constraint_name
                     and tc.table_schema = kcu.table_schema
                    where tc.constraint_type = 'PRIMARY KEY' and tc.table_schema = any(%s)
                    order by tc.table_schema, tc.table_name, kcu.ordinal_position
                    """,
                (requested_schemas,),
            )
            for namespace, name, column in cursor.fetchall():
                if (namespace, name) in resources:
                    resources[(namespace, name)]["primary_key"].append(column)
        return [
            DiscoveredResource(
                external_id=item["external_id"],
                name=item["name"],
                namespace=item["namespace"],
                category=item["category"],
                schema={"fields": item["fields"], "primary_key": item["primary_key"]},
            )
            for item in resources.values()
        ]


POSTGRESQL_CONNECTOR_SCHEMA = {
    "type": "object",
    "required": ["host", "database"],
    "properties": {
        "host": {"type": "string", "title": "Host"},
        "port": {"type": "integer", "default": 5432},
        "database": {"type": "string"},
        "username": {"type": "string", "description": "Prefer storing this in Secret"},
        "schemas": {"type": "array", "items": {"type": "string"}, "default": ["public"]},
        "sslmode": {
            "type": "string",
            "enum": ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"],
            "default": "prefer",
        },
        "connect_timeout": {"type": "integer", "default": 10},
    },
}


CONNECTOR_DEFINITIONS = {
    "postgresql": {
        "id": "postgresql",
        "name": "PostgreSQL",
        "mode": "local",
        "categories": ["table", "view"],
        "config_schema": POSTGRESQL_CONNECTOR_SCHEMA,
        "capabilities": ["test", "discover", "query"],
    }
}

connector_registry: dict[str, Connector] = {"postgresql": PostgreSQLConnector()}


def get_connector(connector_type: str) -> Connector:
    try:
        return connector_registry[connector_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported connector type: {connector_type}") from exc
