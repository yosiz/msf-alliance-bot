from os.path import isfile
from sqlite3 import connect
from apscheduler.triggers.cron import CronTrigger

DB_PATH = "./data/db/database.sqlite3"
BUILD_PATH = "./data/db/build.sql"
UPGRADE_PATH = "./data/db/upgrades"
cxn = connect(DB_PATH, check_same_thread=False)
cur = cxn.cursor()


def with_commit(func):
    def inner(*args, **kwargs):
        func(*args, **kwargs)
        commit()

    return inner


def get_db_version():
    version = field("PRAGMA user_version")
    if version:
        return version
    else:
        return 0


def version_increment(version=None):
    if version is None:
        version = get_db_version()
    execute(f"PRAGMA user_version = {version + 1}")


@with_commit
def build():
    if isfile(BUILD_PATH):
        scriptexec(BUILD_PATH)


@with_commit
def upgrade(version):
    upgrade_file = f"{UPGRADE_PATH}/upgrade_{version}.sql"
    if isfile(upgrade_file):
        scriptexec(upgrade_file)
        version_increment(version)
        print(f"db upgraded to version:{version}")
    else:
        print(f"db version:{version}")


def commit():
    cxn.commit()


def autosave(sched):
    sched.add_job(commit, CronTrigger(second=0))


def close():
    cxn.close()


def field(command, *values):
    cur.execute(command, tuple(values))
    if (fetch := cur.fetchone()) is not None:
        return fetch[0]


def record(command, *values):
    cur.execute(command, tuple(values))
    return cur.fetchone()


def records(command, *values):
    cur.execute(command, tuple(values))
    return cur.fetchall()


def column(command, *values):
    cur.execute(command, tuple(values))
    return [item[0] for item in cur.fetchall()]


def execute(command, *values):
    cur.execute(command, tuple(values))


def multiexec(command, valueset):
    cur.executemany(command, valueset)


def scriptexec(path):
    with open(path, "r", encoding="utf-8") as script:
        cur.executescript(script.read())
