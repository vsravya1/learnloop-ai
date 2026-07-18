"""Shared visual styling for LearnLoop Streamlit pages."""

import streamlit as st


def inject_product_css():
    """Apply the shared product shell without changing page behavior."""
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            html { font-size: 17px; }
            body, [class*="css"] {
                font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                font-size: 17px;
            }
            [data-testid="stAppViewContainer"] { background: #fcfcfe; }
            [data-testid="stMainBlockContainer"], section.main > div.block-container {
                padding-top: 2.25rem;
                padding-bottom: 3rem;
            }
            [data-testid="stSidebar"] {
                background: #f7f6fb;
                border-right: 1px solid #e8e6f0;
            }
            [data-testid="stSidebar"] .block-container { padding: 1.25rem 0.9rem 1.75rem; }
            [data-testid="stSidebarNav"] { padding-top: 0.4rem; }
            [data-testid="stSidebarNav"] a {
                border-radius: 0.55rem;
                margin: 0.14rem 0;
                padding: 0.52rem 0.62rem;
            }
            [data-testid="stSidebarNav"] a[aria-current="page"] {
                background: #ebe8fb;
                color: #4f3fa7;
                font-weight: 600;
            }
            [data-testid="stSidebar"] button {
                border-radius: 0.55rem;
                border-color: #ddd9eb;
            }
            [data-testid="stMetric"] {
                background: #ffffff;
                border: 1px solid #eceaf3;
                border-radius: 0.75rem;
                padding: 0.75rem 0.9rem;
                box-shadow: 0 2px 10px rgba(35, 29, 75, 0.04);
            }
            #MainMenu, footer, header { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )
