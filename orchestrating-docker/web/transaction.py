# transaction.py

from sqlalchemy import text
from app import db, logger


# how to restart a transaciton
# while True:
#   try:
#        ts = startTransaction()
#        all the queries, setting readts or writets to ts
#             after reads, update the read TS of the exact same query second, first do the read query
#             example: read:
#               select from Bags that are red
#               update Bags set readts = :ts, writets = NULL where <read query where>
#             example: write:
#               update Bags set <write action>, writets = ts, readts = NULL where <write query where>
#        endTransaction()
#   except psycopg2.Error:
#       rollBack()
#   else:
#        break

def getTimestamp():
    # Lock the timestamp table while we get and increment the next available timestamp.
    # The timestamp MUST be unique for every transaction.
    begin = text('BEGIN')
    db.engine.execute(begin)
    setTS = text('SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED')
    db.engine.execute(setTS)

    lockTimestamp = text('LOCK TABLE timestamp IN ACCESS EXCLUSIVE MODE')
    db.engine.execute(lockTimestamp)

    queryTimestamp = text('SELECT nextavailable FROM timestamp')
    ts = db.engine.execute(queryTimestamp).fetchone()
    if ts is None:
      createts = text('INSERT INTO timestamp VALUES (0)')
      db.engine.execute(createts)
      queryTimestamp = text('SELECT nextavailable FROM timestamp')
      ts = db.engine.execute(queryTimestamp).fetchone()
    incTimestamp = text('UPDATE timestamp SET nextavailable = :tsInc')
    db.engine.execute(incTimestamp, tsInc = ts.nextavailable + 1)

    end = text('COMMIT')
    db.engine.execute(end)
    return ts

def startTransaction():
    ts = getTimestamp()
    #begin = text('BEGIN')
    #db.engine.execute(begin)
    #setTS = text('SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED')
    #db.engine.execute(setTS)
    logger.info("Transaction %d start", ts.nextavailable)
    return ts.nextavailable

def endTransaction():
    db.session.commit()
    #end = text('COMMIT')
    #db.engine.execute(end)
    logger.info("Transaction commit")

def rollBack():
    #rollback = text('ROLLBACK')
    #db.engine.execute(rollback)
    logger.info("Rolling back...")