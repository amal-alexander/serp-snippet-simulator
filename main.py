import streamlit as st
import pandas as pd
from io import StringIO
import re

# Configure page
st.set_page_config(
    page_title="SERP Snippet Simulator",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Google-like styling
st.markdown("""
<style>
    .serp-preview {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
        font-family: arial, sans-serif;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .serp-title {
        color: #1a0dab;
        font-size: 20px;
        line-height: 1.3;
        margin-bottom: 2px;
        cursor: pointer;
        text-decoration: underline;
        font-weight: normal;
    }
    
    .serp-title:hover {
        text-decoration: underline;
    }
    
    .serp-url {
        color: #006621;
        font-size: 14px;
        line-height: 1.3;
        margin-bottom: 2px;
    }
    
    .serp-description {
        color: #4d5156;
        font-size: 14px;
        line-height: 1.58;
        word-wrap: break-word;
    }
    
    .mobile-preview .serp-title {
        font-size: 18px;
    }
    
    .mobile-preview .serp-url {
        font-size: 13px;
    }
    
    .mobile-preview .serp-description {
        font-size: 13px;
    }
    
    .truncated-text {
        background-color: #fee;
        padding: 2px 4px;
        border-radius: 3px;
        border-left: 3px solid #f56565;
    }
    
    .pixel-counter {
        font-size: 12px;
        color: #666;
        margin-top: 5px;
    }
    
    .warning-icon {
        color: #f56565;
        font-weight: bold;
    }
    
    .success-icon {
        color: #48bb78;
        font-weight: bold;
    }
    
    .metric-card {
        background: #f7fafc;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #4299e1;
    }
</style>
""", unsafe_allow_html=True)

# Custom CSS for FAQ Schema
st.markdown("""
<style>
    .faq-item {
        border-top: 1px solid #e5e7eb;
        padding: 12px 0;
    }
    .faq-question {
        color: #1a0dab;
        font-size: 16px;
        cursor: pointer;
    }
    .faq-question::after {
        content: ' ▼'; /* Simple dropdown indicator */
    }
</style>
""", unsafe_allow_html=True)

# Custom CSS for Review/Rating Schema
st.markdown("""
<style>
    .rating-stars {
        color: #ffc700; /* Google's star color */
        font-size: 16px;
        display: inline-block;
        margin-right: 8px;
    }
    .rating-text {
        color: #4d5156;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

class SERPSimulator:
    def __init__(self):
        # Character width mapping for Google SERP font (more accurate pixel widths)
        self.char_widths = {
            'a': 8.5, 'b': 9, 'c': 8, 'd': 9, 'e': 8, 'f': 5, 'g': 9, 'h': 9, 'i': 4, 'j': 4,
            'k': 8, 'l': 4, 'm': 13, 'n': 9, 'o': 9, 'p': 9, 'q': 9, 'r': 6, 's': 8, 't': 5,
            'u': 9, 'v': 8, 'w': 12, 'x': 8, 'y': 8, 'z': 8,
            'A': 11, 'B': 10, 'C': 11, 'D': 11, 'E': 9, 'F': 9, 'G': 12, 'H': 11, 'I': 4, 'J': 7,
            'K': 10, 'L': 9, 'M': 13, 'N': 11, 'O': 12, 'P': 10, 'Q': 12, 'R': 10, 'S': 10, 'T': 9,
            'U': 11, 'V': 10, 'W': 15, 'X': 10, 'Y': 10, 'Z': 9,
            '0': 9, '1': 9, '2': 9, '3': 9, '4': 9, '5': 9, '6': 9, '7': 9, '8': 9, '9': 9,
            ' ': 4, '.': 4, ',': 4, ':': 4, ';': 4, '!': 4, '?': 8, '-': 5, '_': 8, '(': 5, ')': 5,
            '[': 4, ']': 4, '{': 5, '}': 5, '/': 5, '\\': 5, '|': 4, '@': 16, '#': 9, '$': 9,
            '%': 14, '^': 8, '&': 11, '*': 6, '+': 9, '=': 9, '<': 9, '>': 9, '~': 9, '`': 5,
            '"': 5, "'": 3
        }
        
        # SERP limits (in pixels) - Updated 2024/2025 standards
        self.limits = {
            'desktop': {
                'title': 580,
                'description': 920
            },
            'mobile': {
                'title': 460,  # Stricter mobile limit for ~50-55 chars
                'description': 960  # Updated 2024 mobile limit (~155-160 chars)
            }
        }
    
    def calculate_pixel_width(self, text):
        """Calculate approximate pixel width of text"""
        total_width = 0
        # Use sum() with a generator for a more Pythonic and efficient calculation
        for char in text:
            total_width += self.char_widths.get(char, 9)  # Default width for unknown chars
        return total_width
    
    def truncate_text(self, text, max_pixels):
        """Truncate text based on pixel width limit"""
        if not text:
            return text, False

        if self.calculate_pixel_width(text) <= max_pixels:
            return text, False

        # Ellipsis is 3 dots, each 4px wide.
        ellipsis_width = self.calculate_pixel_width("...")

        # Backtrack from the end of the string to find the right truncation point
        for i in range(len(text) - 1, 0, -1):
            truncated = text[:i]
            if self.calculate_pixel_width(truncated) + ellipsis_width <= max_pixels:
                return truncated + "...", True

        # If no part of the string fits with an ellipsis, return an ellipsis if it fits
        return ("..." if ellipsis_width <= max_pixels else ""), True
    
    def format_url(self, url):
        """Format URL for SERP display"""
        """Format URL for SERP display into a breadcrumb-like path."""
        if not url:
            return "example.com › ..."

        try:
            # Remove protocol and split into domain and path
            clean_url = re.sub(r'^https?://', '', url)
            parts = clean_url.split('/')
            domain = parts[0].replace('www.', '')
            path = [p for p in parts[1:] if p]
            return f"{domain} › {' › '.join(path)}"
        except Exception:
            return url # Fallback to original URL on error

def main():
    # Initialize simulator
    simulator = SERPSimulator()
    
    # Header
    st.title("🔍 SERP Snippet Simulator")
    st.markdown("**Optimize your search snippets with pixel-perfect accuracy**")
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Device toggle
        device_type = st.radio(
            "📱 Device Type",
            ["Desktop", "Mobile"],
            help="Switch between desktop and mobile SERP limits"
        )
        
        # Bulk testing section
        st.header("📊 Bulk Testing")
        uploaded_file = st.file_uploader(
            "Upload CSV file",
            type=['csv'],
            help="Upload a CSV with columns: title, description, url"
        )
        
        if st.button("📋 Download Template CSV"):
            template_df = pd.DataFrame({
                'title': ['Example Title 1', 'Example Title 2'],
                'description': ['Example description 1', 'Example description 2'],
                'url': ['https://example1.com', 'https://example2.com']
            })
            csv = template_df.to_csv(index=False)
            st.download_button(
                label="Download Template",
                data=csv,
                file_name="serp_template.csv",
                mime="text/csv"
            )
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("✏️ Input Fields")
        
        # Input fields
        title = st.text_input(
            "Title Tag",
            placeholder="Enter your page title...",
            help="The clickable headline that appears in search results"
        )
        
        description = st.text_area(
            "Meta Description",
            placeholder="Enter your meta description...",
            height=100,
            help="The descriptive text that appears below the title in search results"
        )
        
        url = st.text_input(
            "URL",
            placeholder="https://example.com/page",
            help="The URL of your page"
        )
        
        schema_type = st.selectbox(
            "Schema Type (Rich Snippet)",
            ["None", "FAQ", "Review/Rating"],
            index=0,
            help="Select a schema type to see how it might appear as a Rich Snippet."
        )
        
        # Calculate metrics
        device_key = device_type.lower()
        title_pixels = simulator.calculate_pixel_width(title)
        desc_pixels = simulator.calculate_pixel_width(description)
        
        title_limit = simulator.limits[device_key]['title']
        desc_limit = simulator.limits[device_key]['description']
        
        # Display metrics
        st.subheader("📏 Metrics")
        
        # Title metrics
        title_status = "✅" if title_pixels <= title_limit else "⚠️"
        st.markdown(f"""
        <div class="metric-card">
            <strong>{title_status} Title:</strong> {len(title)} chars, {title_pixels}px / {title_limit}px<br>
            <small>{'✅ Within limits' if title_pixels <= title_limit else '❌ Exceeds limit - will be truncated'}</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Description metrics
        desc_status = "✅" if desc_pixels <= desc_limit else "⚠️"
        st.markdown(f"""
        <div class="metric-card">
            <strong>{desc_status} Description:</strong> {len(description)} chars, {desc_pixels}px / {desc_limit}px<br>
            <small>{'✅ Within limits' if desc_pixels <= desc_limit else '❌ Exceeds limit - will be truncated'}</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.header("👀 SERP Preview")
        
        # Generate preview
        truncated_title, title_truncated = simulator.truncate_text(title or "Your Page Title", title_limit)
        truncated_desc, desc_truncated = simulator.truncate_text(description or "Your meta description appears here...", desc_limit)
        formatted_url = simulator.format_url(url)
        
        # Preview styling class
        preview_class = "mobile-preview" if device_type == "Mobile" else ""
        
        # Build the HTML for the preview
        schema_html = ""
        if schema_type == "FAQ":
            schema_html = """
            <div style="padding-top: 0; margin-top: -10px; border-top: 1px solid #e5e7eb;">
                <div class="faq-item"><div class="faq-question">What is the first sample question?</div></div>
                <div class="faq-item"><div class="faq-question">What is the second sample question?</div></div>
                <div class="faq-item"><div class="faq-question">What is the third sample question?</div></div>
            </div>
            """
        elif schema_type == "Review/Rating":
            # Prepend rating before the description
            schema_html = """
            <div>
                <span class="rating-stars">★★★★☆</span>
                <span class="rating-text">Rating: 4.5 - 1,234 reviews</span>
            </div>
            """

        # Display preview
        st.markdown(f"""
        <div class="serp-preview {preview_class}">"""
        + f"""<div class="serp-title {'truncated-text' if title_truncated else ''}">{truncated_title}</div>
            <div class="serp-url">{formatted_url}</div>"""
        + (schema_html if schema_type == 'Review/Rating' else '')
        + f"""<div class="serp-description {'truncated-text' if desc_truncated else ''}">{truncated_desc}</div>"""
        + (schema_html if schema_type == 'FAQ' else '')
        + """
        </div>
        """, unsafe_allow_html=True)
        
        # Export options
        st.subheader("💾 Export Options")
        
        # Create export data
        export_data = {
            'Title': title,
            'Description': description,
            'URL': url,
            'Title_Pixels': title_pixels,
            'Title_Truncated': title_truncated,
            'Desc_Pixels': desc_pixels,
            'Desc_Truncated': desc_truncated,
            'Device': device_type,
            'Truncated_Title': truncated_title,
            'Truncated_Description': truncated_desc
        }
        
        # Copy snippet button
        snippet_text = f"{truncated_title}\n{formatted_url}\n{truncated_desc}"
        if st.button("📋 Copy Snippet to Clipboard"):
            st.code(snippet_text, language=None)
            st.success("Snippet ready to copy!")
        
        # Download CSV
        export_df = pd.DataFrame([export_data])
        csv_export = export_df.to_csv(index=False)
        st.download_button(
            label="📊 Download as CSV",
            data=csv_export,
            file_name=f"serp_analysis_{device_type.lower()}.csv",
            mime="text/csv"
        )
    
    # Bulk testing section
    if uploaded_file is not None:
        st.header("📊 Bulk Analysis Results")
        
        try:
            # Read uploaded CSV
            df = pd.read_csv(uploaded_file)
            
            if not all(col in df.columns for col in ['title', 'description', 'url']):
                st.error("CSV must contain columns: title, description, url")
                return
            
            # Process each row
            results = []
            for _, row in df.iterrows():
                title = str(row.get('title', ''))
                description = str(row.get('description', ''))
                title_pixels = simulator.calculate_pixel_width(title)
                desc_pixels = simulator.calculate_pixel_width(description)
                
                truncated_title, title_truncated = simulator.truncate_text(title, title_limit)
                truncated_desc, desc_truncated = simulator.truncate_text(description, desc_limit)
                
                results.append({
                    'Original_Title': row['title'],
                    'Original_Description': row['description'],
                    'URL': row['url'],
                    'Title_Pixels': title_pixels,
                    'Title_OK': title_pixels <= title_limit,
                    'Title_Truncated': title_truncated,
                    'Desc_Pixels': desc_pixels,
                    'Desc_OK': desc_pixels <= desc_limit,
                    'Desc_Truncated': desc_truncated,
                    'Truncated_Title': truncated_title,
                    'Truncated_Description': truncated_desc
                })
            
            results_df = pd.DataFrame(results)
            
            # Display summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Analyzed", len(results_df))
            with col2:
                titles_ok = results_df['Title_OK'].sum()
                st.metric("Titles OK", f"{titles_ok}/{len(results_df)}")
            with col3:
                descs_ok = results_df['Desc_OK'].sum()
                st.metric("Descriptions OK", f"{descs_ok}/{len(results_df)}")
            with col4:
                both_ok = ((results_df['Title_OK']) & (results_df['Desc_OK'])).sum()
                st.metric("Both OK", f"{both_ok}/{len(results_df)}")
            
            # Display results table
            st.dataframe(
                results_df,
                use_container_width=True,
                column_config={
                    "Title_OK": st.column_config.CheckboxColumn("Title ✅"),
                    "Desc_OK": st.column_config.CheckboxColumn("Desc ✅"),
                    "Title_Pixels": st.column_config.NumberColumn("Title px", format="%d"),
                    "Desc_Pixels": st.column_config.NumberColumn("Desc px", format="%d"),
                }
            )
            
            # Download bulk results
            bulk_csv = results_df.to_csv(index=False)
            st.download_button(
                label="📊 Download Bulk Results",
                data=bulk_csv,
                file_name=f"bulk_serp_analysis_{device_type.lower()}.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()