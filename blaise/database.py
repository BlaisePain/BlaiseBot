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

                # ---------------- CONTRACTS ---------------- #

                await cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = 'contracts'
                """)

                exists = await cur.fetchone()

                if exists[0] == 0:
                    await cur.execute("""
                    CREATE TABLE contracts(
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        guild_id BIGINT,
                        message_id BIGINT,
                        creator_id BIGINT,
                        collect_time INT,
                        skills VARCHAR(20),
                        deadline VARCHAR(50),
                        thread_id BIGINT,
                        status VARCHAR(20),
                        end_time DATETIME,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """)

                # ---------------- VACATION CONFIG ---------------- #

                await cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = 'vacation_config'
                """)

                exists = await cur.fetchone()

                if exists[0] == 0:
                    await cur.execute("""
                    CREATE TABLE vacation_config(
                        guild_id BIGINT PRIMARY KEY,
                        panel_channel BIGINT,
                        log_channel BIGINT,
                        vacation_role BIGINT,
                        break_role BIGINT,
                        staff_roles TEXT
                    );
                    """)

                # ---------------- VACATIONS ---------------- #

                await cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = 'vacations'
                """)

                exists = await cur.fetchone()

                if exists[0] == 0:
                    await cur.execute("""
                    CREATE TABLE vacations(
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        guild_id BIGINT,
                        user_id BIGINT,
                        type VARCHAR(20),
                        start_date DATETIME,
                        end_date DATETIME,
                        reminder_sent BOOLEAN DEFAULT FALSE
                    );
                    """)

                # ---------------- VACATION HISTORY ---------------- #

                await cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = 'vacation_history'
                """)

                exists = await cur.fetchone()

                if exists[0] == 0:
                    await cur.execute("""
                    CREATE TABLE vacation_history(
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        guild_id BIGINT,
                        user_id BIGINT,
                        type VARCHAR(20),
                        start_date DATETIME,
                        end_date DATETIME,
                        completed_at DATETIME,
                        early_ended BOOLEAN
                    );
                    """)

                # ---------------- CONTRACT PARTICIPANTS ---------------- #

                await cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = 'contract_participants'
                """)

                exists = await cur.fetchone()

                if exists[0] == 0:
                    await cur.execute("""
                    CREATE TABLE contract_participants(
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        guild_id BIGINT,
                        message_id BIGINT,
                        user_id BIGINT
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

                # ---------------- ACADEMY CONFIG ---------------- #

                await cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = 'academy_config'
                """)

                exists = await cur.fetchone()

                if exists[0] == 0:
                    await cur.execute("""
                    CREATE TABLE academy_config(
                        guild_id BIGINT PRIMARY KEY,
                        role_id BIGINT,
                        category_id BIGINT,
                        log_channel_id BIGINT
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
                        message_id BIGINT,
                        required_roles TEXT
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

    async def set_required_roles(self, guild_id, roles):

        roles = ",".join(map(str, roles))

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                INSERT INTO birthday_config(guild_id,required_roles)
                VALUES(%s,%s)
                ON DUPLICATE KEY UPDATE required_roles=%s
                """, (guild_id, roles, roles))

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
                SELECT channel_id, role_id, required_roles, message_id
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

    # =========================================================
    # ACADEMY CONFIG
    # =========================================================

    async def set_academy_role(self, guild_id, role_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                INSERT INTO academy_config(guild_id, role_id)
                VALUES(%s, %s)
                ON DUPLICATE KEY UPDATE role_id=%s
                """, (guild_id, role_id, role_id))

    async def set_academy_category(self, guild_id, category_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                INSERT INTO academy_config(guild_id, category_id)
                VALUES(%s, %s)
                ON DUPLICATE KEY UPDATE category_id=%s
                """, (guild_id, category_id, category_id))

    async def set_academy_logs(self, guild_id, log_channel_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                INSERT INTO academy_config(guild_id, log_channel_id)
                VALUES(%s, %s)
                ON DUPLICATE KEY UPDATE log_channel_id=%s
                """, (guild_id, log_channel_id, log_channel_id))

    async def get_academy_config(self, guild_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                SELECT role_id, category_id, log_channel_id
                FROM academy_config
                WHERE guild_id=%s
                """, (guild_id,))

                return await cur.fetchone()

    # =========================================================
    # CONTRACTS CONFIG
    # =========================================================

    async def create_contract(self, guild_id, message_id, creator_id, time, skills, deadline, thread_id, end_time,
                              created_at):
        """Creează un contract nou în baza de date"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                INSERT INTO contracts
                (guild_id, message_id, creator_id, collect_time, skills, deadline, thread_id, status, end_time, created_at)
                VALUES(%s, %s, %s, %s, %s, %s, %s, 'collecting', %s, %s)
                """, (guild_id, message_id, creator_id, time, skills, deadline, thread_id, end_time, created_at))

    async def get_contract_count(self, guild_id):
        """Obține numărul de contracte pentru un guild"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                SELECT COUNT(*) 
                FROM contracts 
                WHERE guild_id=%s
                """, (guild_id,))

                result = await cur.fetchone()
                return result[0] if result else 0

    async def get_contract(self, guild_id, message_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("""
                SELECT *
                FROM contracts
                WHERE guild_id=%s AND message_id=%s
                """, (guild_id, message_id))

                return await cur.fetchone()

    async def update_contract_status(self, guild_id, message_id, status):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                UPDATE contracts
                SET status=%s
                WHERE guild_id=%s AND message_id=%s
                """, (status, guild_id, message_id))

    async def add_participant(self, guild_id, message_id, user_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                SELECT id FROM contract_participants
                WHERE guild_id=%s AND message_id=%s AND user_id=%s
                """, (guild_id, message_id, user_id))

                exists = await cur.fetchone()

                if exists:
                    return False

                await cur.execute("""
                INSERT INTO contract_participants(guild_id,message_id,user_id)
                VALUES(%s,%s,%s)
                """, (guild_id, message_id, user_id))

                return True

    async def remove_participant(self, guild_id, message_id, user_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                DELETE FROM contract_participants
                WHERE guild_id=%s AND message_id=%s AND user_id=%s
                """, (guild_id, message_id, user_id))

                return cur.rowcount > 0

    async def get_participants(self, guild_id, message_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                SELECT user_id
                FROM contract_participants
                WHERE guild_id=%s AND message_id=%s
                """, (guild_id, message_id))

                rows = await cur.fetchall()

                return [r[0] for r in rows]

    async def get_all_contracts(self, guild_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("""
                SELECT *
                FROM contracts
                WHERE guild_id=%s
                """, (guild_id,))

                return await cur.fetchall()

    # ================= VACATION =================

    async def set_vacation_config(self, guild_id, panel, logs, vac_role, break_role, staff):

        staff = ",".join(map(str, staff))

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                INSERT INTO vacation_config
                (guild_id,panel_channel,log_channel,vacation_role,break_role,staff_roles)
                VALUES(%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                panel_channel=%s,
                log_channel=%s,
                vacation_role=%s,
                break_role=%s,
                staff_roles=%s
                """, (guild_id, panel, logs, vac_role, break_role, staff,
                      panel, logs, vac_role, break_role, staff))

    async def get_vacation_config(self, guild_id):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                SELECT panel_channel,log_channel,vacation_role,break_role,staff_roles
                FROM vacation_config
                WHERE guild_id=%s
                """, (guild_id,))

                return await cur.fetchone()

    async def create_vacation(self, guild, user, type, start, end):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                INSERT INTO vacations
                (guild_id,user_id,type,start_date,end_date)
                VALUES(%s,%s,%s,%s,%s)
                """, (guild, user, type, start, end))

    async def get_active_vacations(self, guild):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                SELECT user_id,type,start_date,end_date
                FROM vacations
                WHERE guild_id=%s
                """, (guild,))

                return await cur.fetchall()

    async def remove_vacation(self, guild, user):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                DELETE FROM vacations
                WHERE guild_id=%s AND user_id=%s
                """, (guild, user))

    async def add_history(self, guild, user, type, start, end, early):

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                INSERT INTO vacation_history
                (guild_id,user_id,type,start_date,end_date,completed_at,early_ended)
                VALUES(%s,%s,%s,%s,%s,NOW(),%s)
                """, (guild, user, type, start, end, early))