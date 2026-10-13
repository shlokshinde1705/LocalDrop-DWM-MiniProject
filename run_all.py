"""
LocalDrop: Master Pipeline Runner
Author: Ayush Kamble & Shlok Shinde (VIT INFT)
Usage:
  python run_all.py            # Executes full pipeline and launches Flask web app
  python run_all.py --no-server# Runs data gen, ETL, export, and tests without starting server
"""

import os
import sys
import argparse
import subprocess


def main():
    parser = argparse.ArgumentParser(description="LocalDrop Master Runner")
    parser.add_argument("--no-server", action="store_true", help="Run full pipeline and tests without starting Flask server")
    args = parser.parse_args()

    print("====================================================================")
    print("   LOCALDROP: MASTER PIPELINE RUNNER (DWM ACADEMIC MINI-PROJECT)    ")
    print("   Vidyalankar Institute of Technology - Department of IT           ")
    print("   Students: Ayush Kamble (24101C0065), Shlok Shinde (24101C0063)   ")
    print("====================================================================")

    # Step 1: Generate Operational Data
    print("\n[STEP 1/5] Generating Operational Database (db/generate_data.py)...")
    res1 = subprocess.run([sys.executable, os.path.join("db", "generate_data.py")])
    if res1.returncode != 0:
        print("Error during operational data generation!")
        sys.exit(res1.returncode)

    # Step 2: Run ETL Pipeline
    print("\n[STEP 2/5] Executing Data Preprocessing & ETL (etl/etl.py)...")
    res2 = subprocess.run([sys.executable, os.path.join("etl", "etl.py")])
    if res2.returncode != 0:
        print("Error during ETL execution!")
        sys.exit(res2.returncode)

    # Step 3: Export Report Artifacts
    print("\n[STEP 3/5] Exporting Results, CSVs, and PNG Charts (scripts/export_results.py)...")
    res3 = subprocess.run([sys.executable, os.path.join("scripts", "export_results.py")])
    if res3.returncode != 0:
        print("Error during result export!")
        sys.exit(res3.returncode)

    # Step 4: Run Pytest Test Suite
    print("\n[STEP 4/5] Executing Complete Pytest Test Suite (tests/)...")
    res4 = subprocess.run([sys.executable, "-m", "pytest", "tests/"])
    if res4.returncode != 0:
        print("Pytest test failure detected!")
        sys.exit(res4.returncode)

    print("\n" + "="*68)
    print("   ALL PIPELINE STAGES, RECONCILIATION & TESTS PASSED 100%!        ")
    print("="*68)

    # Step 5: Start Flask Application
    if not args.no_server:
        print("\n[STEP 5/5] Launching LocalDrop BI Dashboard on http://127.0.0.1:5000 ...")
        print("Press CTRL+C in this terminal to stop the web server.\n")
        subprocess.run([sys.executable, "app.py"])


if __name__ == "__main__":
    main()
