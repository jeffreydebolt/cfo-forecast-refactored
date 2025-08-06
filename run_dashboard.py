import os
import subprocess
import sys

# Set environment variables to skip welcome screen
os.environ["STREAMLIT_SKIP_WELCOME"] = "true"
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

# Get the absolute path to the dashboard script
# The mapping_review.py is in the same directory as this script
dashboard_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "mapping_review.py"
)

# Run the Streamlit dashboard
subprocess.run([sys.executable, "-m", "streamlit", "run", dashboard_path]) 