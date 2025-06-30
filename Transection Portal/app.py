from flask import Flask, render_template, request, make_response
import io, csv
from datetime import datetime
from utility import fetch_transaction_info

app = Flask(__name__)

INITIATORS = [
    "ALL",
    r"Teletalk\sptest",
    r"Teletalk\teletalk02",
    r"Teletalk\Topu",
    r"MM SP\test123",
    r"Teletalk\raisul6053"
]

@app.route("/", methods=["GET", "POST"])
def index():
    data = []
    cols = []
    csv_text = ""
    selected = "ALL"
    start_date = end_date = ""

    if request.method == "POST":
        selected = request.form.get("initiator", "ALL")
        # Raw date inputs from HTML form (YYYY-MM-DD)
        raw_sd = request.form.get("start_date", "")
        raw_ed = request.form.get("end_date", "")

        if raw_sd and raw_ed:
            # Convert to YYYYMMDDHH24MISS for full-day range
            try:
                sd = datetime.strptime(raw_sd, "%Y-%m-%d").strftime("%Y%m%d") + "000000"
                ed = datetime.strptime(raw_ed, "%Y-%m-%d").strftime("%Y%m%d") + "235959"
                start_date, end_date = raw_sd, raw_ed

                cols, data = fetch_transaction_info(selected, sd, ed)
            except ValueError:
                # Invalid date format; leave data empty
                cols, data = [], []

        # build CSV if data exists
        if data:
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(cols)
            w.writerows(data)
            csv_text = buf.getvalue()

    return render_template(
        "transactions.html",
        initiators=INITIATORS,
        data=data,
        column_names=cols,
        csv_data=csv_text,
        selected=selected,
        start_date=start_date,
        end_date=end_date
    )

@app.route("/download", methods=["POST"])
def download():
    csv_content = request.form["csv_content"]
    initiator = request.form["initiator"].replace("\\", "_")
    filename = f"transactions_{initiator}.csv"
    bom = "\ufeff"
    resp = make_response(bom + csv_content)
    resp.headers["Content-Disposition"] = f"attachment; filename={filename}"
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    return resp

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=6005)
