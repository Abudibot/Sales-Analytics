"""
Sales Analytics Without Pandas

Key design choice : a value is only "repaired" when its meaning is obvious 
(formatting noise such as "38,999" or "KES 18999"). If fixing it would mean guessing ("two", 
"N/A", blank), the whole row is skipped and reported, so totals are never build on 
invented numbers.
"""
import csv
import math
from pathlib import Path 

# Paths are build from the script's own location, so the program works from any folder.
BASE_DIR = Path(__file__).resolve().parent    # Finds the directory containing the script 
DATA_PATH = BASE_DIR / "data" / "electronics_sales.csv"   # Contructs the path to the input file
OUTPUT_PATH = BASE_DIR / "output" / "sales_report.txt"   # Constructs the path for the report

# In 'path: Path = DATA_PATH', 'path' identifies the CSV file to read,
#  and DATA_PATH supplies te default value when no path is provided.

HIGH_VALUE_THRESHOLD = 100_000.0   # An assumption

def read_sales(path: Path = DATA_PATH) -> list[dict[str, str]]:
    """Read the CSV with the csv module and return the raw rows.
    
    DictReader gives each row as a dict keyed by the header names. Every value stays a
    string at this stage; converting to numbers is a separate, deliberate step.
    """
    with open(path, newline="", encoding="utf-8") as f: 
        return list(csv.DictReader(f))

    """
    'open' opens the file, 'with' ensures the file is properly closed after the block 
    finishes, 'newline=""' is the recommended setting when working with the CSV module
    'encoding="utf-8"' supports common text characters, 'as f' gives the open file an alias
    """
def parse_number(value: str) -> float | None:
    """Convert a messy numeric string to a float, or return None if it cannot be trusted.
    
    Accepted: "5999", "38,999" (thousands separator), "KES 18999" (currency prefix).
    Rejected: "", "N/A", "two" and anything else that is not clearlya number. 

    Returning None (instead of raising an error) lets the caller decide what to do with a 
    bad value, which keeps this function small and reusable.
    """ 
    if value is None: 
        return None 
    text = value.strip()       # remove stray spaces 
    if text.upper().startswith("KES"):      # drop a currency prefix 
        text = text[3:].strip() 
    text = text.replace(",","") 
    if not text:                 # empty string -> nothing to parse 
        return None 
    try: 
        number = float(text) 
    except ValueError:         #"two", "N/A", ... -> not trustworthy 
        return None 
    if math.isnan(number) or math.isinf(number):   # float("nan") / float("inf") parse but are junk 
        return None  
    return number

def convert_rows(rows: list[dict[str, str]]) -> tuple[list[dict], list[dict]]:
    """Return (clean_rows, skipped_rows). Clean rows have numeric quantity, unit price and revenue.
    
    For each row: parse quantity and price, then validate them. If anything is wrong the row goes 
    to 'skipped' together with a readable reason. Otherwise it goes to 'clean' with a new 'revenue' 
    field = quantity * unit price .
    """ 
    clean, skipped = [], [] 
    for row in rows: 
        quantity = parse_number(row["quantity"]) 
        price = parse_number(row["unit_price_kes"]) 

        # Find the first problem (if any) and describe it. 
        reason = None  
        if quantity is None: 
            reason = f"invalid quantity '{row['quantity']}'" 
        elif price is None: 
            reason = f"invalid unit price '{row['unit_price_kes']}'" 
        elif quantity <= 0 or price <0: 
            reason = "non-positive quantity or negative price" 

        if reason: 
            skipped.append({**row, "reason": reason}) 
            continue  

        # {**row, ...} copies the original fields and overrides/adds the numeric ones. 
        clean.append({
            **row, 
            "quantity": int(quantity) if quantity == int(quantity) else quantity, 
            "unit_price_kes": price, 
            "revenue": quantity * price, 
        }) 
    return clean, skipped

def total_revenue(rows: list[dict]) -> float:
    return sum(r["revenue"] for r in rows)

def revenue_by(rows: list[dict], field: str) -> dict[str, float]:
    """Total revenue grouped by any column (product, store, payment_method...).
    
    Uses a plain dictionary as an accumulator: .get(key, 0.0) starts a new group at zero 
    the first time a key is seen, then each row's revenue is added to its group,. 
    Because 'field' is a parameter, the same function works for every column.
    """
    totals: dict[str, float] = {} 
    for r in rows: 
        totals[r[field]] = totals.get(r[field], 0.0) + r["revenue"]
    return totals

def top_n(totals: dict[str, float], n: int = 3) -> list[tuple[str, float]]:
    """Return the n highest (key, value) pairs, highest first. 
    
    Sorts the (key, value) pairs by value in descending order and keeps the first n.
    """ 
    return sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:n] 

    """
    totals.items() gives pairs containing each dictionary key and its value 
    key=lambda kv:kv[1] (kv represents one pair, kv[0] is the name, kv[1] is the revenue) 
    the lambda is a small, unnamed function 
    reverse=True, sorts from highesr to lowest
    """
    
def high_value(rows: list[dict], threshold: float) -> list[dict]:
    """Transactions whose revenue is at or above threshold (use a comprehension).
    
    Note '>=': a sale exactly equal to the threshold counts as high-value.
    """ 
    return [r for r in rows if r["revenue"] >= threshold]
    

def mean(values: list[float]) -> float:
    """ Arithmetic average: sum divided by count.""" 
    if not values: 
        raise ValueError("mean() of empty list") 
    return sum(values) / len(values)

def median(values: list[float]) -> float:
    """Middle value of the sorted data (average of the two middle values if the count is even).

    Sorting a copy with sorted() leaves the caller's list untouched. 
    """ 
    if not values: 
        raise ValueError("median() of empty list") 
    ordered = sorted(values) 
    mid = len(ordered) // 2 
    if len(ordered) % 2:        # odd count: exactly one middle item 
        return ordered[mid] 
    return (ordered[mid - 1] + ordered[mid]) / 2     # even count: average the two middle items 

def minimum_maximum(values: list[float]) -> tuple[float, float]:
    """Smallest and largest value found in a single pass (no min()/max() builtins).""" 
    if not values: 
        raise ValueError("minimum_maximum() of empty list") 
    lo = hi = values[0] 
    for v in values[1:]: 
        if v < lo: 
            lo = v 
        if v > hi: 
            hi = v 
    return lo, hi

def verify_with_pandas(path: Path, my_results: dict) -> list[str]:
    """Recompute the headline numbers with pandas and report whethereach one matches.
    This is an independent check: pandas reads the same CSV, cleans it with its own tools,
    and its answers are compared with the pure-Python ones. Returns the report lines so
    they can be printed and saved with the rest of the report.
    """
    import pandas as pd

    lines = ["=== pandas verification ==="]
    df = pd.read_csv(path, dtype=str)
    price_text = (df["unit_price_kes"].str.replace("KES", "", regex=False)
                  .str.replace(",", "", regex=False).str.strip())
        # errors="coerce" turns unparseable text ("two", "N/A", "") into NaN...
    df["qty"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["price"] = pd.to_numeric(price_text, errors="coerce")
        # ...and dropna removes those rows, mirroring the rows we skipped by hand.
    df = df.dropna(subset=["qty", "price"]).copy()
    df["revenue"] = df["qty"] * df["price"]

    def close(a: float, b: float) -> bool:
        """Float-safe comparison (equal within a hair), since == on floats can mislead."""
        return math.isclose(a, b, rel_tol=1e-9, abs_tol=0.005) 
        # function checks whether two numbers are sufficiently close to be treated as equal 
        # math.isclose() uses relative and absolute tolerances to account for small differences.

    def verdict(ok: bool, pure, pand) -> str:
        return "MATCH" if ok else f"MISMATCH (pure={pure}, pandas={pand})"

     # 1) total revenue
    p_total = float(df["revenue"].sum())
    lines.append("Total revenue : " + verdict(close(p_total, my_results["total"]), my_results["total"], p_total))

    # 2) revenue per product (same keys AND same amounts)
    p_prod = df.groupby("product")["revenue"].sum().to_dict()
    ok = p_prod.keys() == my_results["by_product"].keys() and all(
        close(p_prod[k], my_results["by_product"][k]) for k in p_prod)
    lines.append("Revenue by product : " + verdict(ok, my_results["by_product"], p_prod))

    # 3) top 3 products (same names, same order, same amounts)
    p_top = list(df.groupby("product")["revenue"].sum().sort_values(ascending=False).head(3).items())
    ok = [k for k, _ in p_top] == [k for k, _ in my_results["top3"]] and all(
        close(a[1], b[1]) for a, b in zip(p_top, my_results["top3"]))
    lines.append("Top 3 : " + verdict(ok, my_results["top3"], p_top))

    # 4) mean and median of transaction revenue
    p_mean, p_median = float(df["revenue"].mean()), float(df["revenue"].median())
    ok = close(p_mean, my_results["mean"]) and close(p_median, my_results["median"])
    lines.append("Mean / median : " + verdict(
        ok, (my_results["mean"], my_results["median"]), (p_mean, p_median)))
    return lines

def build_report(path: Path = DATA_PATH, output: Path = OUTPUT_PATH) -> str:
    """Run the whole pipeline and produce the text report.

    Flow: read -> clean -> compute every figure -> format into lines -> verify with pandas
    -> print and save. Computing first and formatting second keeps the maths separate from
    the presentation.
     """
    rows = read_sales(path)
    clean, skipped = convert_rows(rows)

    # --- compute everything the report needs ---
    total = total_revenue(clean)
    by_product = revenue_by(clean, "product")
    ranked = top_n(by_product, len(by_product)) # n = number of products -> full ranking
    top3 = top_n(by_product, 3)
    big = high_value(clean, HIGH_VALUE_THRESHOLD)
    revenues = [r["revenue"] for r in clean]
    avg, med = mean(revenues), median(revenues)
    lo, hi = minimum_maximum(revenues)

    # --- format the report, one string per line ---
    # Skipped rows are listed with sale ID + reason so nothing is dropped silently.
    details = ", ".join(f"{s['sale_id']}: {s['reason']}" for s in skipped)
    out = [
        "=== Sales report: September 2026 ===",
        f"Rows read : {len(rows)}",
        f"Rows used : {len(clean)}",
        f"Rows skipped : {len(skipped)}" + (f" ({details})" if skipped else ""),
        "",
        f"Total revenue (KES): {total:,.2f}", # ,.2f = thousands separator + 2 decimals
        "",
        "Revenue by product (KES)",
    ]
    width = max(len(name) for name, _ in ranked) # pad names so the amounts line up
    out += [f" {name:<{width}} {amount:>14,.2f}" for name, amount in ranked]
    out += ["", "Top 3 products"]
    out += [f" {i}. {name} - KES {amount:,.2f}" for i, (name, amount) in enumerate(top3, 1)]
    out += ["", f"High-value transactions (>= KES {HIGH_VALUE_THRESHOLD:,.0f}): {len(big)}"]
    out += [f" {r['sale_id']} {r['sale_date']} {r['store']} {r['product']} KES {r['revenue']:,.2f}"
            for r in big]
    out += [
        "",
        "Transaction revenue statistics",
        f" mean : {avg:,.2f}",
        f" median : {med:,.2f}",
        f" min : {lo:,.2f}",
        f" max : {hi:,.2f}",
        "",
    ]
    out += verify_with_pandas(path, {
        "total": total, "by_product": by_product, "top3": top3,
        "mean": avg, "median": med,
    })
      
    # --- save and show ---
    report = "\n".join(out) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True) # create output/ if it does not exist
    output.write_text(report, encoding="utf-8")
    print(report)
    print(f"Report saved to {output}")
    return report


if __name__ == "__main__":
        build_report()