import json
import os
import uuid

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict

from aidp.modules.catalogs.connectors import PostgreSQLConnector


@pytest.mark.integration
def test_postgresql_connector_against_real_database():
    dsn = os.getenv("AIDP_TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("Set AIDP_TEST_POSTGRES_DSN to run PostgreSQL integration tests")
    params = conninfo_to_dict(dsn)
    schema = f"aidp_test_{uuid.uuid4().hex[:10]}"
    with psycopg.connect(dsn, autocommit=True) as connection, connection.cursor() as cursor:
        cursor.execute(f'create schema "{schema}"')
        cursor.execute(
            f'create table "{schema}".purchase (id uuid primary key, name text not null)'
        )
    try:
        config = {
            "host": params.get("host", "localhost"),
            "port": int(params.get("port", 5432)),
            "database": params["dbname"],
            "schemas": [schema],
            "sslmode": params.get("sslmode", "disable"),
        }
        secret = json.dumps({"username": params["user"], "password": params.get("password", "")})
        connector = PostgreSQLConnector()
        assert connector.test(config, secret)["database"] == params["dbname"]
        resources = connector.discover(config, secret, {"schemas": [schema]})
        assert len(resources) == 1
        assert resources[0].name == "purchase"
        assert resources[0].schema["primary_key"] == ["id"]
        assert [field["name"] for field in resources[0].schema["fields"]] == ["id", "name"]
    finally:
        with psycopg.connect(dsn, autocommit=True) as connection, connection.cursor() as cursor:
            cursor.execute(f'drop schema "{schema}" cascade')
