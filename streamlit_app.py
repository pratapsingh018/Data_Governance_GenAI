import streamlit as st
import sqlite3
import pandas as pd
import yaml
import os
from dotenv import load_dotenv
import requests
import json

# Load environment
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Data Governance Copilot",
    page_icon="🛡️",
    layout="wide"
)

# Load API key
api_key = os.getenv("GEMINI_API_KEY")

def load_data_from_db():
    """Load data from SQLite database"""
    try:
        conn = sqlite3.connect("governance.db")
        df = pd.read_sql("SELECT * FROM adult_income LIMIT 100", conn)
        conn.close()
        return df
    except Exception as e:
        return pd.DataFrame({"Error": [f"Could not load data: {e}"]})

def load_validation_logs():
    """Load validation logs from database"""
    try:
        conn = sqlite3.connect("governance.db")
        logs_df = pd.read_sql("""
            SELECT ts, column_name, row_index, value, message 
            FROM validation_logs 
            ORDER BY ts DESC 
            LIMIT 50
        """, conn)
        conn.close()
        return logs_df
    except Exception as e:
        return pd.DataFrame({"Error": [f"Could not load validation logs: {e}"]})

def load_metadata():
    """Load metadata from YAML file"""
    try:
        with open("metadata.yaml", "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        return {"Error": f"Could not load metadata: {e}"}

def load_policies():
    """Load policies from YAML file"""
    try:
        with open("policy.yaml", "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        return {"Error": f"Could not load policies: {e}"}

def ask_ai_copilot(question):
    """Ask the AI copilot a question using the same logic as simple_qa.py"""
    if not api_key:
        return "❌ API key not configured. Please check your .env file."
    
    # Load context
    context = ""
    
    # Add metadata
    try:
        with open("metadata.yaml", "r") as f:
            context += f"\n# metadata.yaml\n{f.read()}\n"
    except:
        context += "\n# metadata.yaml not found\n"
    
    # Add policies  
    try:
        with open("policy.yaml", "r") as f:
            context += f"\n# policy.yaml\n{f.read()}\n"
    except:
        context += "\n# policy.yaml not found\n"
    
    # Add validation logs
    try:
        conn = sqlite3.connect("governance.db")
        rows = conn.execute("SELECT * FROM validation_logs LIMIT 50").fetchall()
        conn.close()
        if rows:
            context += "\nValidation Issues:\n"
            for r in rows:
                context += f"- Column '{r[2]}' had issue: {r[5]}\n"
    except:
        context += "\nNo validation logs found.\n"
    
    # Make API call
    model = "models/gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": f"You are a Data Governance Copilot. Use the provided context to answer clearly and concisely.\n\nContext: {context}\n\nQuestion: {question}"}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 2048
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"❌ API Error: {response.status_code} - {response.text[:500]}"
    except Exception as e:
        return f"❌ Error: {e}"

# Main app
def main():
    st.title("🛡️ Data Governance Copilot")
    st.markdown("*GenAI-powered data governance assistant for the UCI Adult Income dataset*")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📊 Data Preview", "🔍 Validation Summary", "🤖 Governance Chat"])
    
    # Tab 1: Data Preview
    with tab1:
        st.header("Dataset Preview")
        st.markdown("Showing first 100 rows from the Adult Income dataset")
        
        # Load and display data
        df = load_data_from_db()
        
        if "Error" not in df.columns:
            # Show basic stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rows", len(df))
            with col2:
                st.metric("Total Columns", len(df.columns))
            with col3:
                st.metric("Data Types", len(df.dtypes.unique()))
            
            # Show data
            st.dataframe(df, use_container_width=True)
            
            # Show column info
            st.subheader("Column Information")
            metadata = load_metadata()
            if "columns" in metadata:
                col_info = []
                for col in metadata["columns"]:
                    col_info.append({
                        "Column": col["name"],
                        "Type": col["type"], 
                        "PII": "Yes" if col.get("pii", False) else "No",
                        "Description": col.get("description", "")
                    })
                st.dataframe(pd.DataFrame(col_info), use_container_width=True)
        else:
            st.error(df["Error"].iloc[0])
    
    # Tab 2: Validation Summary  
    with tab2:
        st.header("Data Validation Summary")
        st.markdown("Recent validation checks and any data quality issues")
        
        # Load validation logs
        logs_df = load_validation_logs()
        
        if "Error" not in logs_df.columns and len(logs_df) > 0:
            # Show summary stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Issues", len(logs_df))
            with col2:
                st.metric("Affected Columns", logs_df["column_name"].nunique())
            with col3:
                recent_issues = len(logs_df[pd.to_datetime(logs_df["ts"]) > pd.Timestamp.now() - pd.Timedelta(days=1)])
                st.metric("Recent Issues (24h)", recent_issues)
            
            # Show validation logs
            st.subheader("Validation Issues")
            st.dataframe(logs_df, use_container_width=True)
            
            # Show issues by column
            st.subheader("Issues by Column")
            issue_counts = logs_df["column_name"].value_counts()
            st.bar_chart(issue_counts)
            
        elif "Error" not in logs_df.columns:
            st.success("✅ No validation issues found! Your data quality looks good.")
        else:
            st.error(logs_df["Error"].iloc[0])
        
        # Show current policies
        st.subheader("Active Data Governance Policies")
        policies = load_policies()
        if "policies" in policies:
            for policy in policies["policies"]:
                with st.expander(f"Policy {policy['id']}: {policy.get('rule', 'N/A')}"):
                    st.write(f"**Description:** {policy.get('description', 'No description')}")
                    if "column" in policy:
                        st.write(f"**Applies to column:** {policy['column']}")
                    if "k" in policy:
                        st.write(f"**Minimum group size:** {policy['k']}")
    
    # Tab 3: Governance Chat
    with tab3:
        st.header("🤖 AI Governance Assistant")
        st.markdown("Ask questions about your data governance setup, policies, and data quality")
        
        # Sample questions
        st.subheader("Try asking:")
        sample_questions = [
            "Which columns are marked as PII?",
            "What validation issues were found?",
            "Summarize the current masking policies",
            "What data retention policies are in place?",
            "Are there any data quality concerns I should know about?"
        ]
        
        for i, question in enumerate(sample_questions):
            if st.button(question, key=f"sample_{i}"):
                st.session_state["chat_question"] = question
        
        # Chat interface
        st.subheader("Ask a Question")
        question = st.text_input(
            "Type your question here:",
            value=st.session_state.get("chat_question", ""),
            placeholder="e.g., Which columns contain PII data?"
        )
        
        if st.button("Ask AI Copilot", type="primary"):
            if question:
                with st.spinner("🤖 Thinking..."):
                    answer = ask_ai_copilot(question)
                
                st.subheader("AI Response:")
                st.markdown(answer)
                
                # Clear the question
                st.session_state["chat_question"] = ""
            else:
                st.warning("Please enter a question first!")

if __name__ == "__main__":
    main()