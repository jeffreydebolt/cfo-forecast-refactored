import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase

# Set up page config
st.set_page_config(
    page_title="Forecast Overview",
    layout="wide",
    page_icon="📊"
)

def get_weekly_balance_projection(weeks_ahead=12):
    """Fetch weekly balance projections from Supabase."""
    try:
        res = supabase.rpc('get_weekly_balance_projection', {'weeks_ahead': weeks_ahead}).execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Error fetching balance projections: {str(e)}")
        return pd.DataFrame()

def get_vendor_forecasts():
    """Fetch vendor forecasts and calculate statistics."""
    try:
        # Fetch vendor configurations
        configs = supabase.table('vendors') \
            .select('display_name, forecast_method, forecast_frequency, forecast_day, forecast_amount') \
            .execute()
        
        if not configs.data:
            return pd.DataFrame()
            
        df = pd.DataFrame(configs.data)
        
        # Generate next 4 dates for each vendor
        df['next_dates'] = df.apply(
            lambda r: next_dates(r.forecast_frequency, r.forecast_day), 
            axis=1
        )
        
        # Expand dates and calculate statistics
        df = df.explode('next_dates')
        df['forecast_date'] = pd.to_datetime(df['next_dates'])
        
        # Calculate statistics per vendor
        stats = df.groupby('display_name').agg({
            'forecast_amount': ['mean', 'std'],
            'forecast_frequency': 'first',
            'forecast_method': 'first'
        }).reset_index()
        
        stats.columns = ['display_name', 'avg_amount', 'std_amount', 'frequency', 'method']
        
        # Calculate coefficient of variation (CV)
        stats['cv'] = stats['std_amount'] / stats['avg_amount']
        
        # Get next 4 amounts for each vendor
        next4 = df.sort_values(['display_name', 'forecast_date']) \
            .groupby('display_name') \
            .head(4) \
            .groupby('display_name')['forecast_amount'] \
            .apply(list) \
            .reset_index(name='next4_flows')
        
        # Merge stats with next4 flows
        final_df = stats.merge(next4, on='display_name', how='left')
        
        return final_df
        
    except Exception as e:
        st.error(f"Error fetching vendor forecasts: {str(e)}")
        return pd.DataFrame()

def next_dates(freq, day_or_weekday, start_date=None):
    """Generate next 4 forecast dates based on frequency and day."""
    if start_date is None:
        start_date = datetime.now()
    
    dates = []
    if freq == 'monthly':
        for i in range(4):
            next_month = start_date + relativedelta(months=i)
            if day_or_weekday:
                try:
                    day = int(day_or_weekday)
                    next_date = next_month.replace(day=min(day, 28))
                except ValueError:
                    next_date = next_month
            else:
                next_date = next_month
            dates.append(next_date)
    elif freq == 'weekly':
        weekday_map = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 
                      'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6}
        target_weekday = weekday_map.get(day_or_weekday.lower(), 0)
        
        days_ahead = target_weekday - start_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        
        next_date = start_date + timedelta(days=days_ahead)
        for i in range(4):
            dates.append(next_date + timedelta(weeks=i))
    
    return dates

def create_balance_chart(df):
    """Create an interactive balance projection chart using Plotly."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add balance lines
    fig.add_trace(
        go.Scatter(
            x=df['week_start'],
            y=df['starting_balance'],
            name="Starting Balance",
            line=dict(color='blue')
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(
            x=df['week_start'],
            y=df['ending_balance'],
            name="Ending Balance",
            line=dict(color='green')
        ),
        secondary_y=False
    )
    
    # Add flow bars
    fig.add_trace(
        go.Bar(
            x=df['week_start'],
            y=df['forecasted_flow'],
            name="Net Flow",
            marker_color='rgba(255, 165, 0, 0.5)'
        ),
        secondary_y=True
    )
    
    # Update layout
    fig.update_layout(
        title="Weekly Cash Balance Projection",
        xaxis_title="Week Starting",
        hovermode="x unified",
        showlegend=True,
        height=500
    )
    
    # Update y-axes labels
    fig.update_yaxes(title_text="Balance ($)", secondary_y=False)
    fig.update_yaxes(title_text="Net Flow ($)", secondary_y=True)
    
    return fig

def main():
    st.title("Forecast Overview")
    
    # Weekly Balance Projection Section
    st.header("Weekly Cash Balance Projection")
    
    # Add weeks ahead selector
    weeks_ahead = st.slider("Projection Period (Weeks)", 4, 24, 12)
    
    # Fetch and display balance projections
    balance_df = get_weekly_balance_projection(weeks_ahead)
    if not balance_df.empty:
        # Display the chart
        st.plotly_chart(create_balance_chart(balance_df), use_container_width=True)
        
        # Display the data table
        st.dataframe(
            balance_df,
            column_config={
                "week_start": st.column_config.DateColumn(
                    "Week Starting",
                    format="MMM D, YYYY"
                ),
                "starting_balance": st.column_config.NumberColumn(
                    "Starting Balance",
                    format="$%.2f"
                ),
                "forecasted_flow": st.column_config.NumberColumn(
                    "Net Flow",
                    format="$%.2f"
                ),
                "ending_balance": st.column_config.NumberColumn(
                    "Ending Balance",
                    format="$%.2f"
                )
            },
            hide_index=True
        )
    
    # Vendor Forecasts Section
    st.header("Vendor Forecast Summary")
    
    # Fetch and display vendor forecasts
    vendor_df = get_vendor_forecasts()
    if not vendor_df.empty:
        # Display the summary table
        st.dataframe(
            vendor_df,
            column_config={
                "display_name": "Vendor",
                "frequency": "Frequency",
                "method": "Method",
                "avg_amount": st.column_config.NumberColumn(
                    "Avg Amount",
                    format="$%.2f"
                ),
                "std_amount": st.column_config.NumberColumn(
                    "Std Dev",
                    format="$%.2f"
                ),
                "cv": st.column_config.NumberColumn(
                    "CV",
                    format="%.2f"
                ),
                "next4_flows": st.column_config.ListColumn(
                    "Next 4 Flows",
                    help="Next 4 forecasted amounts"
                )
            },
            hide_index=True
        )
        
        # Show high-variance vendors
        high_var = vendor_df[vendor_df['cv'] > 0.2]
        if not high_var.empty:
            st.subheader("High-Variance Vendors (CV > 20%)")
            st.dataframe(
                high_var[['display_name', 'frequency', 'avg_amount', 'std_amount', 'cv']],
                column_config={
                    "display_name": "Vendor",
                    "frequency": "Frequency",
                    "avg_amount": st.column_config.NumberColumn(
                        "Avg Amount",
                        format="$%.2f"
                    ),
                    "std_amount": st.column_config.NumberColumn(
                        "Std Dev",
                        format="$%.2f"
                    ),
                    "cv": st.column_config.NumberColumn(
                        "CV",
                        format="%.2f"
                    )
                },
                hide_index=True
            )

if __name__ == "__main__":
    main() 