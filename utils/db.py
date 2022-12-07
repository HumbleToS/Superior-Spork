import asyncio

import asyncpg


async def build(user='postgres', password='password', database='superior_spork', host='127.0.0.1'):
    conn = await connect_create_if_not_exists(user=user, password=password, database=database, host=host)
    if conn is not None:
        await conn.execute(
            """
        CREATE TABLE IF NOT EXISTS guilds(
        id bigint PRIMARY KEY,
        added_by bigint,
        prefix text
        );
        """
        )
        await conn.close()
        print("Table(s) created successfully!")


async def connect_create_if_not_exists(user='postgres', password='password', database='superior_spork', host='127.0.0.1'):
    try:
        conn = await asyncpg.connect(user=user, password=password, database=database, host=host)
        print(f"Database '{database}' already exists")
        return conn
    except asyncpg.InvalidCatalogNameError:
        sys_conn = await asyncpg.connect(database='template1', user='postgres')
        await sys_conn.execute('CREATE DATABASE "$1" OWNER "$2"', database, user)
        await sys_conn.close()

        conn = await asyncpg.connect(user=user, password=password, database=database, host=host)
        print(f"Database '{database}' has been created")
        return conn


if __name__ == "__main__":
    asyncio.run(build(user='postgres', password='password', database='superior_spork', host='127.0.0.1'))
