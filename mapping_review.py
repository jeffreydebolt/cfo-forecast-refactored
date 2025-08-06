import streamlit as st
import pandas as pd
import logging
import sys
import os
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_mappings(path="data/vendor_mappings_review.csv"):
    """
    Load vendor mappings from CSV file.
    
    Args:
        path (str): Path to the CSV file
        
    Returns:
        pd.DataFrame: DataFrame containing vendor mappings
    """
    try:
        logger.info(f"Loading mappings from {path}")
        df = pd.read_csv(path, dtype={
            "vendor_name": str,
            "display_name": str,
            "category": str,
            "review_needed": bool,
            "group_locked": bool
        })
        
        # Fill empty categories with "Uncategorized"
        df["category"] = df["category"].fillna("Uncategorized")
        
        logger.info(f"Successfully loaded {len(df)} mappings")
        return df
    except Exception as e:
        logger.error(f"Error loading mappings: {str(e)}")
        st.error(f"Error loading mappings: {str(e)}")
        return pd.DataFrame()

def save_mappings(df, path="data/vendor_mappings_review.csv"):
    """
    Save vendor mappings to CSV file.
    
    Args:
        df (pd.DataFrame): DataFrame containing vendor mappings
        path (str): Path where the CSV file will be saved
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Saving mappings to {path}")
        df.to_csv(path, index=False)
        logger.info("Successfully saved mappings")
        return True
    except Exception as e:
        logger.error(f"Error saving mappings: {str(e)}")
        return False

def update_supabase(df):
    """
    Update vendor mappings in Supabase.
    
    Args:
        df (pd.DataFrame): DataFrame containing vendor mappings
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Updating mappings in Supabase...")
        for _, row in df.iterrows():
            supabase.table("vendors")\
                .update({
                    "display_name": row.display_name,
                    "category": row.category if pd.notna(row.category) else None,
                    "review_needed": bool(row.review_needed),
                    "group_locked": bool(row.group_locked)
                })\
                .eq("vendor_name", row.vendor_name)\
                .execute()
        logger.info("Successfully updated mappings in Supabase")
        return True
    except Exception as e:
        logger.error(f"Error updating Supabase: {str(e)}")
        return False

def main():
    st.set_page_config(page_title="Vendor Display-Name Review", layout="wide")
    
    st.title("Vendor Display-Name Review")
    
    # Load the most recent mapping file
    try:
        mapping_files = sorted([f for f in os.listdir("data") if f.startswith("vendor_mappings_review_")])
        if not mapping_files:
            st.error("No mapping files found. Please run export_vendor_mappings.py first.")
            return
            
        latest_file = os.path.join("data", mapping_files[-1])
        df = load_mappings(latest_file)
        
        if df.empty:
            st.error("No data to display")
            return
            
        # Display file info
        st.info(f"Reviewing mappings from: {latest_file}")
        
        # Add filters
        st.sidebar.header("Filters")
        category_filter = st.sidebar.multiselect(
            "Filter by Category",
            options=sorted(df["category"].unique()),
            default=[]
        )
        
        review_filter = st.sidebar.multiselect(
            "Filter by Review Status",
            options=sorted(df["review_needed"].unique()),
            default=[]
        )
        
        # Apply filters
        if category_filter:
            df = df[df["category"].isin(category_filter)]
        if review_filter:
            df = df[df["review_needed"].isin(review_filter)]
        
        # Display data editor
        st.header("Edit Mappings")
        
        # Get unique categories for the dropdown
        categories = sorted(df["category"].unique())
        
        edited = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "vendor_name": st.column_config.TextColumn(
                    "Vendor Name",
                    help="Original vendor name from transactions",
                    disabled=True
                ),
                "display_name": st.column_config.TextColumn(
                    "Display Name",
                    help="Friendly name for display"
                ),
                "category": st.column_config.TextColumn(
                    "Category",
                    help="Transaction category"
                ),
                "review_needed": st.column_config.CheckboxColumn(
                    "Review Needed",
                    help="Flag for manual review"
                ),
                "group_locked": st.column_config.CheckboxColumn(
                    "Group Locked",
                    help="Prevent automatic grouping"
                )
            }
        )
        
        # Save and Apply button
        if st.button("Save & Apply"):
            with st.spinner("Saving changes..."):
                # Save to CSV
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_path = f"data/vendor_mappings_review_{timestamp}.csv"
                if save_mappings(edited, new_path):
                    # Update Supabase
                    if update_supabase(edited):
                        st.success("Mappings updated successfully!")
                    else:
                        st.error("Failed to update Supabase. Check the logs for details.")
                else:
                    st.error("Failed to save mappings. Check the logs for details.")
                    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        logger.error(f"Error in main: {str(e)}")

if __name__ == "__main__":
    main() 