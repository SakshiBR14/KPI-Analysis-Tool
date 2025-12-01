import pandas as pd
import numpy as np
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from xlsxwriter.utility import xl_col_to_name
import warnings
import os

warnings.filterwarnings('ignore')
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COUNTERS_TO_AVERAGE = [
    'RRC_ConnEstab_Success_Rate',
    'Voice_QoS_Flows_Success_Rate',
    'Data_QoS_Flow_5QI9_Setup_Success_Rate',
    'DRB_@FIVEQI5_Success_Rate',
    'RRC Conn Setup Success Rate',
    'VoNR Call Setup Success Rate',
    'VoNR Call Setup Success Rate_5QI5'
]

POSITIVE_DELTA_GOOD = [
    'RRC_ConnEstabAtt_Sum', 'RRC_ConnEstabSucc_Sum', 'RRC_ConnEstab_Success_Rate', 'DRB_EstabSucc@FIVEQI1',
    'DRB_EstabAtt@FIVEQI1', 'Voice_QoS_Flows_Success_Rate', 'DRB_EstabAtt@FIVEQI9', 'DRB_EstabSucc@FIVEQI9',
    'Data_QoS_Flow_5QI9_Setup_Success_Rate', 'rlc_vol_dl', 'rlc_vol_ul', 'RRU_PrbTotDl', 'RRU_PrbTotUl',
    'RACH_Accessibility_Overall_Success_Rate', 'Cell_Available', 'DRB_EstabSucc@FIVEQI5', 'DRB_EstabAtt@FIVEQI5',
    'DRB_@FIVEQI5_Success_Rate', 'Data_Retainability',
    'UTL_RRC connection attempts', 'RRC Setup Success', 'RRC Conn Setup Success Rate', 'VoNR Call Setup Success Rate',
    'VoNR Call Setup Success Rate_5QI5', 'UTL_Data_Call attempts_5QI09', 'UTL_VoNR_Setup Success_5QI01',
    'DL Data Volume (GB)', 'UL Data Volume (GB)', 'DL Avg PRB Utilization', 'UL Avg PRB Utilization',
    'ACC_RACH Succ Rate_CFRA', 'Cell_Availability(%)', 'VoNR Call Setup Attempt_5QI5',
    'VoNR Call Setup Successes_5QI5', 'Data Retainability', 'VoNR Retainability', 'ACC_Data Accessibility',
    'ACC_VoNR_Accessibility'
]
FAILURE_COUNTERS = ['RRC Failure', 'Voice QOS Failure', 'DRB Failure', 'Cell_Unavailable_Fault', 'RRC Call Drop Rate']

FUNDAMENTAL_KPI_MAP = {
    'RRC_ConnEstabAtt_Sum': 'UTL_RRC connection attempts',
    'RRC_ConnEstabSucc_Sum': 'RRC Setup Success',
    'RRC_ConnEstab_Success_Rate': 'RRC Conn Setup Success Rate',
    'DRB_EstabSucc@FIVEQI1': 'UTL_VoNR_Setup Success_5QI01',
    'DRB_EstabAtt@FIVEQI1': 'UTL_VoNR_Call attempts_5QI01',
    'Voice_QoS_Flows_Success_Rate': 'VoNR Call Setup Success Rate',
    'DRB_EstabAtt@FIVEQI9': 'UTL_Data_Call attempts_5QI09',
    'DRB_EstabSucc@FIVEQI9': 'UTL_Data_Setup Success_5QI09',
    'Data_QoS_Flow_5QI9_Setup_Success_Rate': 'Data_QoS_Flow_5QI9_Setup_Success_Rate',
    'DRB_EstabAtt@FIVEQI5': 'VoNR Call Setup Attempt_5QI5',
    'DRB_EstabSucc@FIVEQI5': 'VoNR Call Setup Successes_5QI5',
    'DRB_@FIVEQI5_Success_Rate': 'VoNR Call Setup Success Rate_5QI5',
    'rlc_vol_dl': 'DL Data Volume (GB)',
    'rlc_vol_ul': 'UL Data Volume (GB)',
    'RRU_PrbTotDl': 'DL Avg PRB Utilization',
    'RRU_PrbTotUl': 'UL Avg PRB Utilization',
    'RACH_Accessibility_Overall_Success_Rate': 'ACC_RACH Succ Rate_CFRA',
    'Cell_Available': 'Cell_Availability(%)',
    'Data_Retainability': 'Data Retainability',
    'Data_Accessibility': 'Data Accessibility',
    'VoNR_Retainability': 'VoNR Retainability',
    'VoNR_Accessibility': 'ACC_VoNR_Accessibility'
}

def classify_delta(pre, post, delta, counter):
    if pd.isna(pre) or pd.isna(post): return 'Counter Missing'
    if pre == 0 and post == 0: return 'No Traffic'
    good_dir = (counter in POSITIVE_DELTA_GOOD and delta >= 0) or \
               (counter not in POSITIVE_DELTA_GOOD and delta <= 0)
    if counter in FAILURE_COUNTERS: return 'Good' if delta <= 0 else 'Bad'
    return 'Good' if good_dir else 'Bad'

def write_summary_sheet(writer, df, sheet_name, is_traffic=False):
    workbook, worksheet = writer.book, writer.book.add_worksheet(sheet_name)
    header_fmt = workbook.add_format({'bg_color': '#4472C4', 'font_color': 'white', 'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
    good_fmt, bad_fmt = workbook.add_format({'bg_color': '#70AD47', 'font_color': 'white', 'bold': True}), workbook.add_format({'bg_color': '#C5504B', 'font_color': 'white', 'bold': True})
    missing_fmt, no_traffic_fmt = workbook.add_format({'bg_color': '#A9A9A9', 'font_color': 'white', 'bold': True}), workbook.add_format({'bg_color': '#C5504B', 'font_color': 'white', 'bold': True, 'align': 'center'})
    proc_traffic_fmt = workbook.add_format({'bg_color': '#70AD47', 'font_color': 'white', 'bold': True, 'align': 'center'})
    for c, val in enumerate(df.columns): worksheet.write(0, c, val, header_fmt)
    for r, row in enumerate(df.values, 1):
        for c, val in enumerate(row):
            s_val = str(val)
            if is_traffic and c > 0:
                if s_val == 'Processing Traffic': worksheet.write(r, c, s_val, proc_traffic_fmt)
                elif s_val == 'No Traffic': worksheet.write(r, c, s_val, no_traffic_fmt)
                else: worksheet.write(r, c, s_val)
            else: worksheet.write(r, c, s_val)
    if not is_traffic:
        for c in range(1, len(df.columns)):
            rng = f'{xl_col_to_name(c)}2:{xl_col_to_name(c)}{len(df)+1}'
            worksheet.conditional_format(rng, {'type': 'text', 'criteria': 'containing', 'value': 'Good', 'format': good_fmt})
            worksheet.conditional_format(rng, {'type': 'text', 'criteria': 'containing', 'value': 'Bad', 'format': bad_fmt})
    for i, col in enumerate(df.columns): worksheet.set_column(i, i, max(df[col].astype(str).map(len).max(), len(col), 12) + 2)

def run_analysis(df, ts_col, group_key, source, analysis_type, time_params):
    available_counters = [col for col in df.columns if col not in [group_key, ts_col] and pd.api.types.is_numeric_dtype(df[col])]
    fname = f'KPI_{analysis_type}_{source}_{group_key.replace(".", "_")}_{datetime.now():%Y%m%d_%H%M%S}.xlsx'

    # Determine the time period string for the new column
    time_period_str = ""
    if analysis_type == 'Validation':
        completion_time = time_params['completion_time']
        time_period_str = f"Pre vs Post {completion_time}"
    elif analysis_type == 'Traffic':
        start_time = time_params['start']
        end_time = time_params['end']
        time_period_str = f"{start_time} to {end_time}"

    with pd.ExcelWriter(fname, engine='xlsxwriter') as writer:
        summary_df = None
        if analysis_type == 'Validation':
            completion_time_dt = datetime.strptime(time_params['completion_time'], '%Y-%m-%d %H:%M:%S')
            summary_data = []
            for identifier in df[group_key].unique():
                group_df = df[df[group_key] == identifier]
                post_df, pre_df = group_df[group_df[ts_col] >= completion_time_dt], group_df[group_df[ts_col] < completion_time_dt]

                if post_df.empty or pre_df.empty: continue

                pre_avg, post_avg = pre_df[available_counters].mean(), post_df[available_counters].mean()
                delta = post_avg - pre_avg

                status_dict = {}
                for col in available_counters:
                    if col in COUNTERS_TO_AVERAGE:
                        avg_val = post_avg.get(col)
                        status_dict[col] = f"{avg_val:.2f}%" if pd.notna(avg_val) else "N/A"
                    else:
                        status_dict[col] = classify_delta(pre_avg.get(col), post_avg.get(col), delta.get(col), col)

                summary_data.append([identifier] + [status_dict.get(k, "Not Found") for k in available_counters])
            
            summary_df = pd.DataFrame(summary_data, columns=[group_key] + available_counters)
            # Insert the new Time Period column at the second position
            summary_df.insert(1, 'Time Period Selected', time_period_str)

        elif analysis_type == 'Traffic':
            start, end = datetime.strptime(time_params['start'], '%Y-%m-%d %H:%M:%S'), datetime.strptime(time_params['end'], '%Y-%m-%d %H:%M:%S')
            df = df[(df[ts_col] >= start) & (df[ts_col] <= end)]
            if df.empty: raise ValueError("No data in time range.")

            summary = df.groupby(group_key)[available_counters].mean().reset_index()
            status_df = summary[[group_key]].copy()

            for col in available_counters:
                if col in COUNTERS_TO_AVERAGE:
                    status_df[col] = summary[col].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
                else:
                    status_df[col] = summary[col].apply(lambda x: 'Processing Traffic' if pd.notna(x) and x > 0 else 'No Traffic')
            
            summary_df = status_df
            # Insert the new Time Period column at the second position
            summary_df.insert(1, 'Time Period Selected', time_period_str)

        if summary_df is not None:
            # Write the 'All KPI Summary' sheet
            write_summary_sheet(writer, summary_df, 'All KPI Summary', is_traffic=(analysis_type == 'Traffic'))

            # Create the 'Fundamental KPI Summary' DataFrame
            fundamental_df = summary_df[[group_key]].copy()
            # Insert the new Time Period column here as well
            fundamental_df.insert(1, 'Time Period Selected', time_period_str)
            
            for mta_name, piworks_name in FUNDAMENTAL_KPI_MAP.items():
                source_col = mta_name if source == 'MTA' else piworks_name
                if source_col in summary_df.columns:
                    fundamental_df[mta_name] = summary_df[source_col]
            
            # Write the 'Fundamental KPI Summary' sheet
            write_summary_sheet(writer, fundamental_df, 'Fundamental KPI Summary', is_traffic=(analysis_type == 'Traffic'))

    messagebox.showinfo("Success", f"Analysis complete! File saved as {fname}")

def get_and_prepare_df(file_path):
    if not file_path or not os.path.exists(file_path):
        return pd.DataFrame(), None

    if file_path.lower().endswith('.csv'):
        df = pd.read_csv(file_path, low_memory=False)
    else:
        df = pd.read_excel(file_path)

    ts_col = next((col for col in df.columns if col.upper() in ['TIMESTAMP', 'DATETIME']), None)
    if not ts_col: raise ValueError("Timestamp column (TIMESTAMP/DATETIME) not found.")

    all_kpi_cols = set(list(FUNDAMENTAL_KPI_MAP.keys()) + list(FUNDAMENTAL_KPI_MAP.values()))
    for col in df.columns:
        if col in all_kpi_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    for col in COUNTERS_TO_AVERAGE:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: x * 100 if pd.notna(x) and x > 0 and x <= 1 else x)

    rate_calculations = {
        'RRC_ConnEstab_Success_Rate': ('RRC_ConnEstabSucc_Sum', 'RRC_ConnEstabAtt_Sum'),
        'Voice_QoS_Flows_Success_Rate': ('DRB_EstabSucc@FIVEQI1', 'DRB_EstabAtt@FIVEQI1'),
        'DRB_@FIVEQI5_Success_Rate': ('DRB_EstabSucc@FIVEQI5', 'DRB_EstabAtt@FIVEQI5'),
        'RRC Conn Setup Success Rate': ('RRC Setup Success', 'UTL_RRC connection attempts'),
        'VoNR Call Setup Success Rate': ('UTL_VoNR_Setup Success_5QI01', 'UTL_VoNR_Call attempts_5QI01'),
        'VoNR Call Setup Success Rate_5QI5': ('VoNR Call Setup Successes_5QI5', 'VoNR Call Setup Attempt_5QI5')
    }

    for rate_col, (num, den) in rate_calculations.items():
        if rate_col not in df.columns and num in df.columns and den in df.columns:
            numerator = pd.to_numeric(df[num], errors='coerce').fillna(0)
            denominator = pd.to_numeric(df[den], errors='coerce').fillna(0)
            df[rate_col] = np.where(denominator > 0, (numerator / denominator) * 100, 0)

    # Convert to datetime objects once and reuse
    df[ts_col] = pd.to_datetime(df[ts_col], errors='coerce', dayfirst=True).dt.tz_localize(None)
    df.dropna(subset=[ts_col], inplace=True)
    return df, ts_col

class KPIValidatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("KPI Validator"); self.geometry("950x700")
        self.font_title, self.font_header = ("Helvetica", 34, "bold"), ("Helvetica", 14, "bold")
        self.font_normal, self.font_normal_bold = ("Helvetica", 12), ("Helvetica", 12, "bold")
        self.font_button = ("Helvetica", 18, "bold")
        self._create_widgets()

    def _create_widgets(self):
        frame_bg, border, title_c, text_c, hover_c = ("#F8F9FA", "#343A40"), ("#DEE2E6", "#495057"), ("#1f6aa5", "#4472C4"), ("#212529", "#DEE2E6"), ("#4682B4", "#4682B4")
        main = ctk.CTkFrame(self, corner_radius=0); main.pack(fill="both", expand=True)
        title_fr = ctk.CTkFrame(main); title_fr.pack(pady=(15, 10), padx=30, fill="x")
        title = ctk.CTkLabel(title_fr, text="KPI Validator", text_color=title_c); title.configure(font=self.font_title); title.pack(pady=5)

        sec_style = {"fg_color": frame_bg, "corner_radius": 15, "border_width": 2, "border_color": border}

        main_options_fr = ctk.CTkFrame(main, **sec_style); main_options_fr.pack(fill="x", padx=30, pady=10)

        src_fr = ctk.CTkFrame(main_options_fr, fg_color="transparent"); src_fr.pack(fill="x", padx=15, pady=10)
        lbl_src = ctk.CTkLabel(src_fr, text="1. Input Source:", text_color=text_c, width=120, anchor="w"); lbl_src.configure(font=self.font_header); lbl_src.pack(side="left")
        self.source_var = tk.StringVar(value="MTA")

        source_button = ctk.CTkSegmentedButton(src_fr, values=["MTA", "PiWorks"], variable=self.source_var, command=lambda v: self._source_changed())
        source_button.pack(side="left", padx=15)

        file_fr = ctk.CTkFrame(main_options_fr, fg_color="transparent"); file_fr.pack(fill="x", padx=15, pady=(0,10))
        lbl_file = ctk.CTkLabel(file_fr, text="2. Data File:", text_color=text_c, width=120, anchor="w"); lbl_file.configure(font=self.font_header); lbl_file.pack(side="left")
        self.file_entry = ctk.CTkEntry(file_fr, height=35, placeholder_text="No file selected...", corner_radius=10, border_width=2); self.file_entry.configure(font=self.font_normal); self.file_entry.pack(side="left", fill="x", expand=True)
        btn_browse = ctk.CTkButton(file_fr, text="Browse", command=self._select_file, width=100, height=35, corner_radius=10, hover_color=hover_c); btn_browse.configure(font=self.font_normal_bold); btn_browse.pack(side="left", padx=(10,0))

        key_fr = ctk.CTkFrame(main_options_fr, fg_color="transparent"); key_fr.pack(fill="x", padx=15, pady=(0,10))
        lbl_key = ctk.CTkLabel(key_fr, text="3. Group By:", text_color=text_c, width=120, anchor="w"); lbl_key.configure(font=self.font_header); lbl_key.pack(side="left")
        self.key_combo = ctk.CTkComboBox(key_fr, values=[], width=250, height=30); self.key_combo.configure(font=self.font_normal); self.key_combo.pack(side="left")

        mode_fr = ctk.CTkFrame(main, **sec_style); mode_fr.pack(fill="x", padx=30, pady=10)
        lbl_mode = ctk.CTkLabel(mode_fr, text="4. Analysis Mode:", text_color=text_c); lbl_mode.configure(font=self.font_header); lbl_mode.pack(anchor="w", padx=15, pady=(10, 5))
        self.mode_var = tk.StringVar(value="Pre/Post")

        mode_button = ctk.CTkSegmentedButton(mode_fr, values=["Pre/Post", "Initial KPI Attempts Check"], variable=self.mode_var, command=self._toggle_mode)
        mode_button.pack(fill="x", padx=15, pady=5)

        disclaimer_label = ctk.CTkLabel(mode_fr, text="*Pre/Post mode is still under testing - Don't use this feature to conclude validation.",
                                        font=(self.font_normal[0], self.font_normal[1], "italic"), text_color="gray")
        disclaimer_label.pack(anchor="w", padx=15, pady=(0, 10))

        self.completion_fr, self.overall_fr = ctk.CTkFrame(main, **sec_style), ctk.CTkFrame(main, **sec_style)
        
        lbl_comp_ts = ctk.CTkLabel(self.completion_fr, text="Completion Timestamp:", text_color=text_c)
        lbl_comp_ts.configure(font=self.font_header)
        lbl_comp_ts.pack(anchor="w", padx=15, pady=(10, 5))
        ts_selector_frame = ctk.CTkFrame(self.completion_fr, fg_color="transparent")
        ts_selector_frame.pack(anchor="w", padx=15, pady=(0, 10))
        self.ts_entry = ctk.CTkEntry(ts_selector_frame, placeholder_text="YYYY-MM-DD HH:MM:SS", width=260, height=30)
        self.ts_entry.configure(font=self.font_normal)
        self.ts_entry.pack(side="left")
        ts_btn = ctk.CTkButton(ts_selector_frame, text="Select", width=60, height=30, command=lambda: self._open_timestamp_selector(self.ts_entry))
        ts_btn.pack(side="left", padx=5)

        lbl_overall_period = ctk.CTkLabel(self.overall_fr, text="Analysis Period:", text_color=text_c)
        lbl_overall_period.configure(font=self.font_header)
        lbl_overall_period.pack(anchor="w", padx=15, pady=(10, 5))
        p_in = ctk.CTkFrame(self.overall_fr, fg_color="transparent")
        p_in.pack(fill="x", padx=15, pady=(0, 10))
        
        lbl_start = ctk.CTkLabel(p_in, text="Start:")
        lbl_start.configure(font=self.font_normal_bold)
        lbl_start.pack(side="left")
        self.start_entry = ctk.CTkEntry(p_in, placeholder_text="Select start time", width=180, height=30)
        self.start_entry.configure(font=self.font_normal)
        self.start_entry.pack(side="left", padx=5)
        start_btn = ctk.CTkButton(p_in, text="Select", width=60, height=30, command=lambda: self._open_timestamp_selector(self.start_entry))
        start_btn.pack(side="left", padx=5)

        lbl_end = ctk.CTkLabel(p_in, text="End:")
        lbl_end.configure(font=self.font_normal_bold)
        lbl_end.pack(side="left", padx=(10,0))
        self.end_entry = ctk.CTkEntry(p_in, placeholder_text="Select end time", width=180, height=30)
        self.end_entry.configure(font=self.font_normal)
        self.end_entry.pack(side="left", padx=5)
        end_btn = ctk.CTkButton(p_in, text="Select", width=60, height=30, command=lambda: self._open_timestamp_selector(self.end_entry))
        end_btn.pack(side="left", padx=5)
        
        btn_fr = ctk.CTkFrame(main); btn_fr.pack(pady=20, fill="x", padx=30)
        self.run_btn = ctk.CTkButton(btn_fr, text="Run Analysis", command=self.submit, height=55, corner_radius=15, fg_color=("#3B8ED0", "#2196F3"), hover_color=("#367AB2", "#1976D2")); self.run_btn.configure(font=self.font_button); self.run_btn.pack(expand=True, fill='x')
        self.prog_bar = ctk.CTkProgressBar(main, height=20)
        
        self._toggle_mode()

    def _select_file(self):
        fp = filedialog.askopenfilename(filetypes=[("Data files", "*.xlsx *.xls *.csv")])
        if fp:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, fp)
            self._load_metadata()

    def _source_changed(self, value=None):
        self._update_grouping_keys()

    def _update_grouping_keys(self):
        keys = ['label.CUCPID', 'label.DUID', 'label.AOI', 'Label.NRCGI'] if self.source_var.get() == "MTA" else ['BASESTATION_CU', 'BASESTATION', 'AOI', 'CELLNAME']
        
        current_selection = self.key_combo.get()
        available_keys = []
        
        try:
            df, _ = get_and_prepare_df(self.file_entry.get())
            if not df.empty:
                available_keys = [k for k in keys if k in df.columns]
        except Exception:
            available_keys = [] 

        self.key_combo.configure(values=available_keys)
        
        if current_selection in available_keys:
            self.key_combo.set(current_selection)
        elif available_keys:
            self.key_combo.set(available_keys[0])
        else:
            self.key_combo.set("")

    def _load_metadata(self):
        self._update_grouping_keys()
        try:
            self.ts_entry.delete(0, tk.END)
            self.start_entry.delete(0, tk.END)
            self.end_entry.delete(0, tk.END)

            df, ts_col = get_and_prepare_df(self.file_entry.get())
            if not df.empty and ts_col:
                timestamps = sorted(df[ts_col].dropna().unique())
                if timestamps:
                    # Format for display
                    last_ts = pd.to_datetime(timestamps[-1]).strftime('%Y-%m-%d %H:%M:%S')
                    first_ts = pd.to_datetime(timestamps[0]).strftime('%Y-%m-%d %H:%M:%S')
                    self.ts_entry.insert(0, last_ts)
                    self.start_entry.insert(0, first_ts)
                    self.end_entry.insert(0, last_ts)
        except Exception as e:
            if self.file_entry.get(): messagebox.showerror("Metadata Error", str(e))

    def _toggle_mode(self, value=None):
        if self.mode_var.get() == "Pre/Post":
            self.completion_fr.pack(fill="x", padx=30, pady=10)
            self.overall_fr.pack_forget()
        else:
            self.overall_fr.pack(fill="x", padx=30, pady=10)
            self.completion_fr.pack_forget()
            
    # --- MODIFIED: Robust, two-step timestamp selector ---
    def _open_timestamp_selector(self, target_entry):
        try:
            df, ts_col = get_and_prepare_df(self.file_entry.get())
            if df.empty or not ts_col:
                messagebox.showinfo("Info", "Load a data file first.", parent=self)
                return
            
            all_timestamps = df[ts_col].dropna().unique()
            timestamps_by_date = {}
            for ts_np in all_timestamps:
                ts = pd.to_datetime(ts_np)
                date_str = ts.strftime('%Y-%m-%d')
                time_str = ts.strftime('%H:%M:%S')
                if date_str not in timestamps_by_date:
                    timestamps_by_date[date_str] = []
                timestamps_by_date[date_str].append(time_str)
            
            unique_dates = sorted(timestamps_by_date.keys())
            if not unique_dates:
                messagebox.showinfo("Info", "No valid timestamps found.", parent=self)
                return
        except Exception as e:
            messagebox.showerror("Error", f"Could not load timestamps: {e}", parent=self)
            return

        picker = ctk.CTkToplevel(self)
        picker.title("Select Timestamp")
        picker.geometry("500x400")
        picker.transient(self)
        picker.attributes("-topmost", True) # Keep window on top without aggressive grab
        picker.after(100, picker.lift)

        # Style for standard tkinter widgets
        listbox_bg = "#2B2B2B"
        listbox_fg = "#DCE4EE"
        select_bg = "#1F6AA5"
        select_fg = "#FFFFFF"

        main_frame = ctk.CTkFrame(picker, fg_color="transparent")
        main_frame.pack(padx=10, pady=(5,0), fill="both", expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(main_frame, text="1. Select Date", font=self.font_normal_bold).grid(row=0, column=0, pady=(0,5))
        ctk.CTkLabel(main_frame, text="2. Select Time", font=self.font_normal_bold).grid(row=0, column=1, pady=(0,5))

        # Date List (Left)
        date_frame = tk.Frame(main_frame, bg=listbox_bg)
        date_frame.grid(row=1, column=0, sticky="nsew", padx=(0,5))
        date_scrollbar = tk.Scrollbar(date_frame, orient="vertical")
        date_listbox = tk.Listbox(date_frame, yscrollcommand=date_scrollbar.set, bg=listbox_bg, fg=listbox_fg, selectbackground=select_bg, selectforeground=select_fg, font=self.font_normal, borderwidth=0, highlightthickness=0, exportselection=False)
        date_scrollbar.config(command=date_listbox.yview)
        date_scrollbar.pack(side="right", fill="y")
        date_listbox.pack(side="left", fill="both", expand=True)
        for date in unique_dates:
            date_listbox.insert(tk.END, date)

        # Time List (Right)
        time_frame = tk.Frame(main_frame, bg=listbox_bg)
        time_frame.grid(row=1, column=1, sticky="nsew", padx=(5,0))
        time_scrollbar = tk.Scrollbar(time_frame, orient="vertical")
        time_listbox = tk.Listbox(time_frame, yscrollcommand=time_scrollbar.set, bg=listbox_bg, fg=listbox_fg, selectbackground=select_bg, selectforeground=select_fg, font=self.font_normal, borderwidth=0, highlightthickness=0, exportselection=False)
        time_scrollbar.config(command=time_listbox.yview)
        time_scrollbar.pack(side="right", fill="y")
        time_listbox.pack(side="left", fill="both", expand=True)

        def on_date_select(event=None):
            try:
                selected_indices = date_listbox.curselection()
                if not selected_indices: return
                
                selected_date = date_listbox.get(selected_indices[0])
                time_listbox.delete(0, tk.END)
                times_for_date = sorted(timestamps_by_date.get(selected_date, []))
                for time in times_for_date:
                    time_listbox.insert(tk.END, time)
            except Exception as e:
                messagebox.showerror("Selection Error", f"An error occurred: {e}", parent=picker)
        
        date_listbox.bind("<<ListboxSelect>>", on_date_select)

        def set_selection():
            date_indices = date_listbox.curselection()
            time_indices = time_listbox.curselection()
            if not date_indices or not time_indices:
                messagebox.showwarning("Incomplete Selection", "Please select both a date and a time.", parent=picker)
                return
            
            selected_date = date_listbox.get(date_indices[0])
            selected_time = time_listbox.get(time_indices[0])
            full_timestamp = f"{selected_date} {selected_time}"
            
            target_entry.delete(0, tk.END)
            target_entry.insert(0, full_timestamp)
            picker.destroy()

        select_button = ctk.CTkButton(picker, text="Select Timestamp", font=self.font_normal_bold, command=set_selection)
        select_button.pack(pady=10, padx=10, fill="x")


    def submit(self):
        self.run_btn.configure(text="Processing...", state="disabled"); self.prog_bar.set(0); self.prog_bar.pack(pady=10, fill='x', padx=30)
        def process():
            try:
                if not self.file_entry.get(): raise ValueError("Please select a file.")
                group_key = self.key_combo.get()
                if not group_key: raise ValueError("Please select a 'Group By' option.")
                
                source = self.source_var.get()
                df, ts_col = get_and_prepare_df(self.file_entry.get())
                
                mode = self.mode_var.get()
                analysis_type = "Validation" if mode == "Pre/Post" else "Traffic"
                
                time_params = {'completion_time': self.ts_entry.get()} if analysis_type == "Validation" else {'start': self.start_entry.get(), 'end': self.end_entry.get()}
                run_analysis(df, ts_col, group_key, source, analysis_type, time_params)
            except Exception as e: messagebox.showerror("Analysis Error", f"An error occurred: {e}")
            finally: self.run_btn.configure(text="Run Analysis", state="normal"); self.prog_bar.pack_forget()
        self.after(100, process)

if __name__ == "__main__":
    app = KPIValidatorApp()
    app.mainloop()
