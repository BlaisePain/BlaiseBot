import aiomysql
import os
from dotenv import load_dotenv

load_dotenv()


class Database:

    def __init__(self):
        self.pool = None

    async def connect(self):

        self.pool = await aiomysql.create_pool(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME"),
            autocommit=True
        )

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:

                # ---------------- APPLICATIONS ---------------- #

                await cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = 'applications'
                """)

                exists = await cur.fetchone()

                if exists[0] == 0:
                    await cur.execute("""
                    CREATE TABLE applications (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id BIGINT,
                        user_name VARCHAR(100),
                        ic_name VARCHAR(70),
                        age INT,
                        history TEXT,
                        motivation VARCHAR(128),
                        online VARCHAR(60),
                        status VARCHAR(20) DEFAULT 'pending',
                        handled_by BIGINT NULL,
                        handled_by_name VARCHAR(100),
                        reason TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """)
                # ----------------APP CONFIG----------------- #
                await cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = 'apply_config'
                """)

                exists = await cur.fetchone()

                if exists[0] == 0:
                    await cur.execute("""
                    CREATE TABLE apply_config(
                        guild_id BIGINT PRIMARY KEY,
                        application_channel BIGINT,
                        log_channel BIGINT,
                        staff_roles TEXT,
                        accept_role BIGINT,
                        remove_role BIGINT,
                        ticket_panel_channel BIGINT
                    );
                    """)


                # ---------------- BIRTHDAYS ---------------- #

                await cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = 'birthdays'
                """)

                exists = await cur.fetchone()

                if exists[0] == 0:
                    await cur.execute("""
                    CREATE TABLE birthdays(
                        user_id BIGINT PRIMARY KEY,
                        display_name VARCHAR(100),
                        day INT,
                        month INT
                    );
                    """)

                # ---------------- CONFIG ---------------- #

                await cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = 'birthday_config'
                """)

                exists = await cur.fetchone()

                if exists[0] == 0:
                    await cur.execute("""
                    CREATE TABLE birthday_config(
                        guild_id BIGINT PRIMARY KEY,
                        channel_id BIGINT,
                        role_id BIGINT,
                        message_id BIGINT
                    );
                    """)

    # =========================================================
    # APPLICATION SYSTEM
    # =========================================================

    async def create_application(self, user_id, user_name, ic_name, age, history, motivation, online):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:

                await cur.execute("""
                INSERT INTO applications
                (user_id, user_name, ic_name, age, history, motivation, online)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (user_id, user_name, ic_name, age, history, motivation, online))

                return cur.lastrowid

    async def get_user_applications(self, user_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:

                await cur.execute("""
                SELECT ic_name, age, history, motivation, online, status, created_at, reason
                FROM applications
                WHERE user_id=%s
                ORDER BY id DESC
                """, (user_id,))

                return await cur.fetchall()

    async def get_application_by_id(self, app_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:

                await cur.execute("""
                SELECT user_id
                FROM applications
                WHERE id=%s
                """, (app_id,))

                return await cur.fetchone()

    async def update_status(self, app_id, status, handled_by, handled_name, reason=None):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:

                await cur.execute("""
                UPDATE applications
                SET status=%s,
                handled_by=%s,
                handled_by_name=%s,
                reason=%s
                WHERE id=%s
                """, (status, handled_by, handled_name, reason, app_id))

    # =========================================================
    # BIRTHDAY SYSTEM
    # =========================================================

    async def set_birthday(self, user_id, display_name, day, month):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:

                await cur.execute("""
                INSERT INTO birthdays(user_id,display_name,day,month)
                VALUES(%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                display_name=%s,
                day=%s,
                month=%s
                """, (user_id, display_name, day, month,
                      display_name, day, month))

    async def remove_birthday(self, user_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:

                await cur.execute("""
                DELETE FROM birthdays
                WHERE user_id=%s
                """, (user_id,))

    async def get_birthdays(self):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:

                await cur.execute("""
                SELECT user_id, display_name, day, month
                FROM birthdays
                """)

                return await cur.fetchall()

    async def get_today_birthdays(self, day, month):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:

                await cur.execute("""
                SELECT user_id, display_name
                FROM birthdays
                WHERE day=%s AND month=%s
                """, (day, month))

                return await cur.fetchall()

    async def delete_birthday(self, user_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:

                await cur.execute("""
                DELETE FROM birthdays
                WHERE user_id=%s
                """, (user_id,))

    # =========================================================
    # BIRTHDAY CONFIG
    # =========================================================

    async def set_channel(self, guild_id, channel_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:

                await cur.execute("""
                INSERT INTO birthday_config(guild_id,channel_id)
                VALUES(%s,%s)
                ON DUPLICATE KEY UPDATE channel_id=%s
                """, (guild_id, channel_id, channel_id))

    async def set_role(self, guild_id, role_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:

                await cur.execute("""
                INSERT INTO birthday_config(guild_id,role_id)
                VALUES(%s,%s)
                ON DUPLICATE KEY UPDATE role_id=%s
                """, (guild_id, role_id, role_id))

    async def set_message(self, guild_id, message_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:

                await cur.execute("""
                INSERT INTO birthday_config(guild_id,message_id)
                VALUES(%s,%s)
                ON DUPLICATE KEY UPDATE message_id=%s
                """, (guild_id, message_id, message_id))

    async def get_config(self, guild_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:

                await cur.execute("""
                SELECT channel_id, role_id, message_id
                FROM birthday_config
                WHERE guild_id=%s
                """, (guild_id,))

                return await cur.fetchone()

            # =========================================================
            # APP CONFIG
            # =========================================================

    async def set_apply_channel(self, guild_id, channel_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                INSERT INTO apply_config(guild_id,application_channel)
                VALUES(%s,%s)
                ON DUPLICATE KEY UPDATE application_channel=%s
                """, (guild_id, channel_id, channel_id))

    async def set_apply_logs(self, guild_id, channel_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                INSERT INTO apply_config(guild_id,log_channel)
                VALUES(%s,%s)
                ON DUPLICATE KEY UPDATE log_channel=%s
                """, (guild_id, channel_id, channel_id))

    async def set_apply_staff(self, guild_id, roles):

        roles = ",".join(map(str, roles))

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                INSERT INTO apply_config(guild_id,staff_roles)
                VALUES(%s,%s)
                ON DUPLICATE KEY UPDATE staff_roles=%s
                """, (guild_id, roles, roles))

    async def set_apply_accept(self, guild_id, role_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                INSERT INTO apply_config(guild_id,accept_role)
                VALUES(%s,%s)
                ON DUPLICATE KEY UPDATE accept_role=%s
                """, (guild_id, role_id, role_id))

    async def set_apply_remove(self, guild_id, role_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                INSERT INTO apply_config(guild_id,remove_role)
                VALUES(%s,%s)
                ON DUPLICATE KEY UPDATE remove_role=%s
                """, (guild_id, role_id, role_id))

    async def get_apply_config(self, guild_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                SELECT application_channel, log_channel, staff_roles, accept_role, remove_role, ticket_panel_channel
                FROM apply_config
                WHERE guild_id=%s
                """, (guild_id,))

                return await cur.fetchone()

    async def set_apply_panel_channel(self, guild_id, channel_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                INSERT INTO apply_config(guild_id,ticket_panel_channel)
                VALUES(%s,%s)
                ON DUPLICATE KEY UPDATE ticket_panel_channel=%s
                """, (guild_id, channel_id, channel_id))