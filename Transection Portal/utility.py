import oracledb

def fetch_transaction_info(initiator, start_date, end_date):
    """
    Returns (column_names, rows) for the TRANSACTIONS query,
    filtering by date range and optionally by a single initiator.
    Assumes TIMESTAMP fields stored as 'YYYYMMDDHH24MISS'.

    The INITIATOR column in output shows only the substring after backslash '\'
    if present, else the full INITIATOR string.
    """
    user = 
    password =
    dsn =

    conn = oracledb.connect(user=user, password=password, dsn=dsn)
    cursor = conn.cursor()

    # handle VARCHAR fields as bytes (to avoid decoding issues)
    def output_bytes(cursor, metadata):
        if metadata.type_code == oracledb.DB_TYPE_VARCHAR:
            return cursor.var(str, arraysize=cursor.arraysize, bypass_decode=True)
    cursor.outputtypehandler = output_bytes

    # Main query with INITIATOR output trimmed after backslash
    base_query = """
    SELECT
        TO_CHAR(TO_DATE(TRANSACTION_INITIATED_TIME, 'YYYYMMDDHH24MISS'), 'DD/MM/RRRR HH24:MI:SS') AS TRANSACTION_INITIATED_TIME,
        TO_CHAR(TO_DATE(TRANSACTION_FINISH_TIME,  'YYYYMMDDHH24MISS'), 'DD/MM/RRRR HH24:MI:SS') AS TRANSACTION_FINISH_TIME,

        TRANSACTION_ID,
        TRANSACTION_TYPE,
        REASON_TYPE,
        CHANNEL,
        TRANSACTION_STATUS,
        FAILURE_REASON,

        -- Extract part after backslash
        CASE
          WHEN INSTR(INITIATOR, '\\') > 0 THEN SUBSTR(INITIATOR, INSTR(INITIATOR, '\\') + 1)
          ELSE INITIATOR
        END AS INITIATOR,

        CREDIT_PARTY_IDENTIFIER,
        CREDIT_PARTY_NAME,
        ACTUAL_AMOUNT,
        CREDIT_ACCOUNT_BALANCE_BEFORE,
        CREDIT_ACCOUNT_BALANCE_AFTER,
        REASON,
        PARENT_OF_CREDIT_PARTY,

        TO_CHAR(SYSDATE, 'DD/MM/RRRR HH24:MI:SS') AS QUERY_EXECUTED_TIME

    FROM TRANSACTIONS
    WHERE TRANSACTION_TYPE = 'E-money Distribute'
      AND (:bind_initiator = 'ALL' OR INITIATOR = :bind_initiator)
      AND TRANSACTION_FINISH_TIME BETWEEN :bind_start AND :bind_end
    ORDER BY TRANSACTION_FINISH_TIME DESC
    """

    params = {
        "bind_initiator": initiator or 'ALL',
        "bind_start": start_date,
        "bind_end": end_date
    }

    cursor.execute(base_query, params)

    column_names = [col[0] for col in cursor.description]

    rows = []
    for row in cursor.fetchall():
        # decode bytes as latin-1, else keep value as is
        rows.append([
            val.decode('latin-1') if isinstance(val, bytes) else val
            for val in row
        ])

    cursor.close()
    conn.close()

    return column_names, rows
