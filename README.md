# Day 2 - Sales Analytics Without Pandas 
Analyses September 2026 electronics sales from 'data/electronics_sales.csv' using only the Python standard library. Pandas is used only at the end to cross-check the results. 
## Approach 
Read the CSV with 'csv.DictReader' (all values start as text). 
Clean numbers with 'parse_numbers', then 'convert_rows' builds clean rows and a list of skipped rows with reasons. 
Calculate total revenue, revenue by product (dictionary) and the top 3. 
Filter high-value transactions with a list comprehension. 
Calculate mean, median, min and max with hand-written functions. 
Write the report to 'output/sales_report.txt'. 
Verify the results with pandas. 
## How to run 
'''bash 
python -m venv venv 
source venv/Scripts/activate 
pip install -r requirements.txt 
python sales_analysis.py 
'''

The report prints in the terminal and is saved to 'output/sales_report.txt' 

## Rules for bad numeric values 
| Raw value | Example | Action| 
|-----------|---------|-------|
| Thousands separator | '38,999' | commas removed | 
| Currency prefix | 'KES 18999' | prefix removed | 
| Empty or missing | (blank) | row skipped |
| Placeholder | 'N/A' | row skipped | 
| Number as a word | 'two' | row skipped | 
| Quantity <= or negative price | | row skipped | 

Skipped rows are listed in the report with their sale ID and reason. 

## Assumptions 
-Revenue = quantity * unit price (KES). 
-A value is repaired only when  its meaning is obvious, otherwise the row is skipped' so  totals  never rely  on guesses. 
-High-value threshold is KES 100,000 (the brief gives none).
