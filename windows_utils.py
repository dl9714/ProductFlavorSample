import time
import json
import hashlib
import copy
import sys # For checking loaded modules for PyQt5

# --- Globals for Caching ---
_cache_get_open_windows = {}
_cache_get_monitor_info = {}
_cache_get_process_info = {}

CACHE_TIMEOUT_SECONDS = 1.5
PROCESS_INFO_CACHE_TIMEOUT_SECONDS = 5.0

# --- Determine if pywin32 is available (for dummy functions) ---
PYWIN32_AVAILABLE = False
try:
    import win32gui
    import win32process
    import win32api
    from PyQt5.QtWidgets import QHeaderView 
except ImportError:
    print("pywin32 or PyQt5.QtWidgets.QHeaderView not found, using dummy/minimal versions.")
    if 'QHeaderView' not in globals():
        class QHeaderView:
            class ResizeMode: Stretch = 0; ResizeToContents = 1; Interactive = 2; Fixed = 3
            def __init__(self, orientation, parent=None): pass
            def setSectionResizeMode(self, col, mode): pass
            def resizeSection(self, col, width): pass

# --- Function Definitions ---
if PYWIN32_AVAILABLE:
    def get_open_windows():
        global _cache_get_open_windows; cache_ts=_cache_get_open_windows.get('timestamp',0);
        if 'data' in _cache_get_open_windows and (time.time()-cache_ts < CACHE_TIMEOUT_SECONDS): return _cache_get_open_windows['data']
        windows = []; 실제hwnd목록 = []; win32gui.EnumWindows(lambda hwnd,param: param.append(hwnd), 실제hwnd목록)
        for hwnd in 실제hwnd목록:
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd): windows.append((hwnd, win32gui.GetWindowText(hwnd)))
        _cache_get_open_windows['data'] = windows; _cache_get_open_windows['timestamp'] = time.time(); return windows
    def get_monitor_info():
        global _cache_get_monitor_info; cache_ts=_cache_get_monitor_info.get('timestamp',0);
        if 'data' in _cache_get_monitor_info and (time.time()-cache_ts < CACHE_TIMEOUT_SECONDS): return _cache_get_monitor_info['data']
        monitors = [{'id':i,'handle':m[0].handle,'rect':win32api.GetMonitorInfo(m[0])['Monitor'],'work_rect':win32api.GetMonitorInfo(m[0])['Work'],'is_primary':win32api.GetMonitorInfo(m[0])['Flags']==win32api.MONITORINFOF_PRIMARY} for i,m in enumerate(win32api.EnumDisplayMonitors(None,None))]
        _cache_get_monitor_info['data']=monitors; _cache_get_monitor_info['timestamp']=time.time(); return monitors
    def get_process_info(hwnd):
        global _cache_get_process_info;cached_entry=_cache_get_process_info.get(hwnd);cache_ts=cached_entry.get('timestamp',0) if cached_entry else 0;
        if cached_entry and (time.time()-cache_ts<PROCESS_INFO_CACHE_TIMEOUT_SECONDS): return cached_entry['data']
        try: _,pid=win32process.GetWindowThreadProcessId(hwnd);handle=win32api.OpenProcess(win32process.PROCESS_QUERY_INFORMATION|win32process.PROCESS_VM_READ,False,pid);path=win32process.GetModuleFileNameEx(handle,0);win32api.CloseHandle(handle);process_data=(pid,path)
        except Exception: process_data=(None,None)
        _cache_get_process_info[hwnd]={'data':process_data,'timestamp':time.time()}; return process_data
    def get_window_details_real(hwnd):pid,path=get_process_info(hwnd);title=win32gui.GetWindowText(hwnd);class_name=win32gui.GetClassName(hwnd);process_name=path.split("\\")[-1] if path else ""; return{'pid':pid,'title':title,'process_name':process_name,'class_name':class_name,'hwnd':hwnd}
else: # Dummy functions
    _DUMMY_OPEN_WINDOWS_DATA = [(100, "Dummy Window App1 (PID 123)"), (200, "Dummy Window App2 (PID 456)"), (300, "Dummy Calc (PID 789)")]
    _DUMMY_PROCESS_INFO_MAP = {100:(123,"C:\\path\\to\\App1.exe"), 200:(456,"C:\\path\\to\\App2.exe"), 300:(789,"C:\\Windows\\System32\\calc.exe")}
    _DUMMY_CLASS_NAME_MAP = {100:"App1MainClass", 200:"App2MainClass", 300:"CalcClass"}
    def get_open_windows():global _cache_get_open_windows;cache_ts=_cache_get_open_windows.get('timestamp',0);if 'data' in _cache_get_open_windows and (time.time()-cache_ts<CACHE_TIMEOUT_SECONDS):return _cache_get_open_windows['data'];_cache_get_open_windows['data']=list(_DUMMY_OPEN_WINDOWS_DATA);_cache_get_open_windows['timestamp']=time.time();return _cache_get_open_windows['data']
    def get_monitor_info():global _cache_get_monitor_info;cache_ts=_cache_get_monitor_info.get('timestamp',0);if 'data' in _cache_get_monitor_info and (time.time()-cache_ts<CACHE_TIMEOUT_SECONDS):return _cache_get_monitor_info['data'];_cache_get_monitor_info['data']=[{'id':0,'handle':0,'rect':(0,0,1920,1080),'work_rect':(0,0,1920,1040),'is_primary':True}];_cache_get_monitor_info['timestamp']=time.time();return _cache_get_monitor_info['data']
    def get_process_info(hwnd):global _cache_get_process_info;cached_entry=_cache_get_process_info.get(hwnd);cache_ts=cached_entry.get('timestamp',0) if cached_entry else 0;if cached_entry and (time.time()-cache_ts<PROCESS_INFO_CACHE_TIMEOUT_SECONDS):return cached_entry['data'];process_data=_DUMMY_PROCESS_INFO_MAP.get(hwnd,(None,None));_cache_get_process_info[hwnd]={'data':process_data,'timestamp':time.time()};return process_data
    def get_window_details_dummy(hwnd):pid,path=get_process_info(hwnd);title=dict(_DUMMY_OPEN_WINDOWS_DATA).get(hwnd,"");class_name=_DUMMY_CLASS_NAME_MAP.get(hwnd,"UnknownClass");process_name=path.split("\\")[-1] if path else "";return{'pid':pid,'title':title,'process_name':process_name,'class_name':class_name,'hwnd':hwnd}

def invalidate_get_open_windows_cache():global _cache_get_open_windows; _cache_get_open_windows.clear()
def invalidate_get_monitor_info_cache():global _cache_get_monitor_info; _cache_get_monitor_info.clear()
def invalidate_get_process_info_cache(hwnd=None):global _cache_get_process_info; (_cache_get_process_info.pop(hwnd,None) if hwnd is not None else _cache_get_process_info.clear())

# --- Mock Qt classes ---
if 'QObject' not in globals(): class QObject: def __init__(self,parent=None):pass
if 'QWidget' not in globals() or not hasattr(QWidget,'layout'):
    class QWidget(QObject):
        def __init__(self,parent=None):super().__init__(); self.accepted=False; self._font=QFont(); self._rect=QRect(0,0,100,100); self._visible=True; self._window_title=""
        def font(self):return self._font;
        def rect(self):return self._rect;
        def size(self):return self._rect.size();
        def update(self):pass;
        def isVisible(self):return self._visible;
        def layout(self): return getattr(self, '_layout', None)
        def setLayout(self, layout): self._layout = layout
        def setWindowTitle(self, title): self._window_title = title
        def exec_(self): print(f"{self.__class__.__name__}.exec_() called (simulating modal)"); self.show(); return 1
        def accept(self): print(f"{self.__class__.__name__}.accept() called"); self.accepted = True; self.close()
        def reject(self): print(f"{self.__class__.__name__}.reject() called"); self.accepted = False; self.close()
        def show(self): pass #print(f"{self.__class__.__name__}.show() called")
        def close(self): pass #print(f"{self.__class__.__name__}.close() called")

if 'QRect' not in globals(): class QRect:def __init__(self,l,t,w,h):self.l,self.t,self.w,self.h=int(l),int(t),int(w),int(h);def left(self):return self.l;def top(self):return self.t;def width(self):return self.w;def height(self):return self.h;def size(self): return QSize(self.w, self.h); def __eq__(self,o): return isinstance(o,QRect) and all(getattr(self,a)==getattr(o,a) for a in 'ltwh');def __repr__(self): return f"QRect({self.l},{self.t},{self.w},{self.h})"
if 'QSize' not in globals(): class QSize:def __init__(self,w,h):self.w,self.h=int(w),int(h);def width(self):return self.w;def height(self):return self.h;def __eq__(self,o):return isinstance(o,QSize) and self.w==o.w and self.h==o.h;def __repr__(self): return f"QSize({self.w},{self.h})"
if 'QFont' not in globals(): class QFont:def __init__(self,n="Arial",s=10):self.name,self.size=n,s
if 'QTableWidgetItem' not in globals():
    class QTableWidgetItem:
        def __init__(self,text=""): self._text=str(text); self._flags = Qt.ItemIsEnabled|Qt.ItemIsSelectable|Qt.ItemIsEditable
        def text(self): return self._text
        def setText(self,text): self._text=str(text)
        def flags(self): return self._flags
        def setFlags(self, flags): self._flags = flags
if 'QTableWidget' not in globals():
    class QTableWidget(QWidget):
        def __init__(self,r=0,c=0,p=None):super().__init__(p);self._rowCount=r;self._columnCount=c;self._items={};self._headers=[];self._cell_widgets={}; self._header_view=QHeaderView(None)
        def rowCount(self):return self._rowCount
        def setRowCount(self,r):self._rowCount=r
        def columnCount(self):return self._columnCount
        def setColumnCount(self,c):self._columnCount=c
        def setItem(self,r,c,item):self._items[(r,c)]=item
        def item(self,r,c):return self._items.get((r,c), QTableWidgetItem(""))
        def insertRow(self,r):self.setRowCount(self.rowCount()+1)
        def setHorizontalHeaderLabels(self,h):self._headers=list(h)
        def horizontalHeader(self): return self._header_view
        def resizeColumnsToContents(self):pass; def resizeRowsToContents(self):pass
        def clearContents(self): self._items.clear(); self._cell_widgets.clear(); self.setRowCount(0)
        def setCellWidget(self,r,c,widget): self._cell_widgets[(r,c)] = widget
        def cellWidget(self,r,c): return self._cell_widgets.get((r,c))

if 'QDialog' not in globals(): class QDialog(QWidget): pass
if 'QVBoxLayout' not in globals(): class QVBoxLayout(QObject): def __init__(self,p=None):super().__init__();self.widgets=[]; def addWidget(self,w):self.widgets.append(w); def addLayout(self,l):pass
if 'QHBoxLayout' not in globals(): class QHBoxLayout(QObject): def __init__(self,p=None):super().__init__();self.items=[]; def addStretch(self,s=1):self.items.append(f"Stretch({s})"); def addWidget(self,w):self.items.append(w)
if 'QPushButton' not in globals(): class QPushButton(QWidget): def __init__(self,t="",p=None):super().__init__(p);self.text=t;self.clicked=MockSignal()
if 'MockSignal' not in globals(): class MockSignal: def __init__(self): self.connections=[]; def connect(self,slot):self.connections.append(slot); def emit(self,*args,**kwargs): [c(*args,**kwargs) for c in self.connections]
if 'QCheckBox' not in globals():
    class QCheckBox(QWidget):
        def __init__(self,t="",p=None):super().__init__(p);self.text=t;self._checked=False;self.stateChanged=MockSignal()
        def setChecked(self,c):self._checked=bool(c)
        def isChecked(self):return self._checked
        def setToolTip(self,tip):self.toolTip = tip
if 'QLineEdit' not in globals(): class QLineEdit(QWidget): def __init__(self,t="",p=None):super().__init__(p);self.text_val=t;self.setText=lambda t:setattr(self,'text_val',t);self.text=lambda:self.text_val;self.setPlaceholderText=lambda t:None
if 'Qt' not in globals():
    class Qt: ItemIsEnabled=32;ItemIsSelectable=1;ItemIsEditable=2;AlignCenter=4;ElideRight=0;AlignLeft=1;AlignTop=32;TextWordWrap=0;DashLine=2;SolidLine=1;GlobalColor={};Antialiasing=1;NoBrush=0;SolidPattern=1;black=0;lightGray=0;blue=0;darkRed=0;WindowModal=2; class AlignmentFlag: AlignCenter=4

class SettingsWindow(QDialog):
    def __init__(self, parent=None): super().__init__(parent); self.layout_edit_table = QTableWidget(); setattr(self.layout_edit_table, 'r', 0)
    def _resize_rows_synced(self):pass
    def _add_item_to_edit_table(self,item_data,perform_resize=True):setattr(self.layout_edit_table,'r',self.layout_edit_table.r+1);self.layout_edit_table.setRowCount(self.layout_edit_table.r);idx=self.layout_edit_table.r-1;self.layout_edit_table.setItem(idx,0,QTableWidgetItem(item_data.get('name','N/A')));self.layout_edit_table.setItem(idx,1,QTableWidgetItem(item_data.get('path','N/A')));self.layout_edit_table.setItem(idx,2,QTableWidgetItem(item_data.get('args','N/A')));if perform_resize:self._resize_rows_synced()
    def load_layout_for_editing(self,layout_data):setattr(self.layout_edit_table,'r',0); self.layout_edit_table.clearContents();[self._add_item_to_edit_table(p,perform_resize=False)for p in layout_data.get('programs',[])];[self._add_item_to_edit_table(layout_data['windows'][w_key],perform_resize=False)for w_key in layout_data.get('windows',{})]; True if self.layout_edit_table.rowCount()>0 and self._resize_rows_synced() else None
    def handle_window_checkbox_state_changed(self,h,t,c):self._add_item_to_edit_table({'title':t})
    def add_program_from_file(self,p,n=None,a=""):self._add_item_to_edit_table({'name':n or p,'path':p})

class LayoutPreviewWidget(QWidget):
    def __init__(self,parent=None):super().__init__(parent);self.monitor_info=[];self.layout_data={};self.virtual_screen_rect=None;self._cached_monitor_elements=[];self._cached_window_elements=[];self._cache_valid_for_size=None;self._cache_valid_for_vs_rect=None;self._cache_valid_for_monitor_info_hash=None;self._cache_valid_for_layout_data_hash=None;self.update_display_info()
    def _generate_data_hash(self,d):return hashlib.md5(json.dumps(d,sort_keys=True,default=str).encode()).hexdigest() if d else "none"
    def update_display_info(self,fr=False):self.monitor_info=get_monitor_info();self._cache_valid_for_monitor_info_hash=None;self._cache_valid_for_vs_rect=None
    def set_layout_data(self,d):self.layout_data=d;self._cache_valid_for_layout_data_hash=None
    def paintEvent(self,e):pass

class EditLayoutLinksDialog(QDialog):
    COLUMN_HWND=0;COLUMN_TITLE=1;COLUMN_PATH=2;COLUMN_URL=3;COLUMN_DUPLICATE=4
    def __init__(self,parent=None,layout_data_ref=None,all_layouts_data=None):
        super().__init__(parent);self.layout_data_ref=layout_data_ref if layout_data_ref is not None else{};self.all_layouts_data=all_layouts_data if all_layouts_data is not None else{};self.changes_made=False;self._hwnd_map={};self._row_widgets={}
        self.setWindowTitle("Edit Launch Links");self.setMinimumSize(600,300);self.table_widget=QTableWidget(0,5,self);self.table_widget.setHorizontalHeaderLabels(["HWND","Title","Launch Path","Launch URL","중복 실행"])
        header=self.table_widget.horizontalHeader();
        if header: header.setSectionResizeMode(self.COLUMN_HWND,QHeaderView.ResizeMode.Interactive);header.setSectionResizeMode(self.COLUMN_TITLE,QHeaderView.ResizeMode.Stretch);header.setSectionResizeMode(self.COLUMN_PATH,QHeaderView.ResizeMode.Stretch);header.setSectionResizeMode(self.COLUMN_URL,QHeaderView.ResizeMode.Stretch);header.setSectionResizeMode(self.COLUMN_DUPLICATE,QHeaderView.ResizeMode.ResizeToContents);header.resizeSection(self.COLUMN_DUPLICATE,80);header.resizeSection(self.COLUMN_HWND,60)
        layout=QVBoxLayout(self);layout.addWidget(self.table_widget);self.button_box=QHBoxLayout();self.ok_button=QPushButton("OK",self);self.cancel_button=QPushButton("Cancel",self);self.button_box.addStretch(1);self.button_box.addWidget(self.ok_button);self.button_box.addWidget(self.cancel_button);layout.addLayout(self.button_box);self.setLayout(layout)
        self.ok_button.clicked.connect(self.accept);self.cancel_button.clicked.connect(self.reject);self.populate_table()
    def populate_table(self):
        self.table_widget.clearContents();self.table_widget.setRowCount(0);self._hwnd_map.clear();self._row_widgets.clear()
        windows_data=self.layout_data_ref.get("windows",{});row=0
        for hwnd_str,win_info in windows_data.items():
            self.table_widget.insertRow(row);self._hwnd_map[row]=hwnd_str;self._row_widgets.setdefault(row,{})
            hwnd_item=QTableWidgetItem(hwnd_str);flags=hwnd_item.flags();hwnd_item.setFlags(flags&~Qt.ItemIsEditable);self.table_widget.setItem(row,self.COLUMN_HWND,hwnd_item)
            title_item=QTableWidgetItem(win_info.get('title','N/A'));flags=title_item.flags();title_item.setFlags(flags&~Qt.ItemIsEditable);self.table_widget.setItem(row,self.COLUMN_TITLE,title_item)
            self.table_widget.setItem(row,self.COLUMN_PATH,QTableWidgetItem(win_info.get('launch_path','')));self.table_widget.setItem(row,self.COLUMN_URL,QTableWidgetItem(win_info.get('launch_url','')))
            allow_dup=win_info.get('allow_duplicate_launch',False);cb=QCheckBox();cb.setChecked(allow_dup);cb.setToolTip("체크 시 레이아웃 적용 시 이미 실행 중이어도 새로 실행합니다.")
            cw=QWidget();cl=QHBoxLayout(cw);cl.addWidget(cb);cl.setAlignment(Qt.AlignmentFlag.AlignCenter);cl.setContentsMargins(0,0,0,0);self.table_widget.setCellWidget(row,self.COLUMN_DUPLICATE,cw);self._row_widgets[row]['duplicate_checkbox']=cb;row+=1
        self.table_widget.resizeColumnsToContents()
    def accept(self):
        if not self.layout_data_ref or"windows"not in self.layout_data_ref:super().accept();return
        layout_windows_ref=self.layout_data_ref["windows"];initial_changes_made_state=self.changes_made
        for row in range(self.table_widget.rowCount()):
            hwnd_str=self._hwnd_map.get(row);
            if not hwnd_str or hwnd_str not in layout_windows_ref:continue
            win_info=layout_windows_ref[hwnd_str];op=win_info.get('launch_path');ou=win_info.get('launch_url');od=win_info.get('allow_duplicate_launch',False)
            np_text=self.table_widget.item(row,self.COLUMN_PATH).text().strip();nu_text=self.table_widget.item(row,self.COLUMN_URL).text().strip();nad=self._row_widgets[row]['duplicate_checkbox'].isChecked()
            np_val=f'"{np_text}"'if np_text and not(np_text.startswith('"')and np_text.endswith('"'))else np_text if np_text else None
            if np_val:(op!=np_val)and(setattr(win_info,'launch_path',np_val)or setattr(self,'changes_made',True))
            elif'launch_path'in win_info:win_info.pop('launch_path');setattr(self,'changes_made',True)
            nu_val=nu_text if nu_text else None
            if nu_val:(ou!=nu_val)and(setattr(win_info,'launch_url',nu_val)or setattr(self,'changes_made',True))
            elif'launch_url'in win_info:win_info.pop('launch_url');setattr(self,'changes_made',True)
            if od!=nad:win_info['allow_duplicate_launch']=nad;self.changes_made=True
        if self.changes_made and not initial_changes_made_state:print(f"  EditLayoutLinksDialog: Changes made to '{self.layout_data_ref.get('name','N/A')}'.")
        super().accept()

class MainWindow(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.layouts_data={"layout1":{"name":"Layout 1","windows":{"100":{"title":"Window A","obj":QObject(),"process_name":"App1.exe","class_name":"Class1","launch_path":"\"C:\\Program Files\\App1\\app1.exe\"","allow_duplicate_launch":False,"mock_orig_pid":1000},"101":{"title":"Window B","obj":QObject(),"process_name":"App2.exe","class_name":"Class2","launch_url":"www.example.com","allow_duplicate_launch":True,"mock_orig_pid":1001}}},"layout2":{"name":"Layout 2","apps":[{"path":"app.exe"}]}}
        self.projects_data={"project1":{"name":"Project 1","layouts":["layout1"],"version":1,"settings":QObject()}}
        self.current_selected_layout_name="layout1";self.launched_processes={};self.settings={'time_to_wait_for_apps_to_launch_pass_1':0.01,'time_to_wait_for_new_windows_pass_3':0.01}
    def get_layout_data_from_active_project(self,layout_name):return self.layouts_data.get(layout_name)
    def open_link_editor_for_selected_layout(self,layout_name=None):
        name_to_edit=layout_name or self.current_selected_layout_name;layout_data_ref=self.get_layout_data_from_active_project(name_to_edit)
        if not layout_data_ref:print(f"  Layout '{name_to_edit}' not found.");return None
        dialog=EditLayoutLinksDialog(parent=self,layout_data_ref=layout_data_ref,all_layouts_data=self.layouts_data)
        if name_to_edit=="layout1" and "100" in layout_data_ref.get("windows",{}): # Simulate edits for testing
            target_row = next((r for r,h in dialog._hwnd_map.items() if h=="100"),-1)
            if target_row!=-1:
                dialog.table_widget.item(target_row,EditLayoutLinksDialog.COLUMN_PATH).setText("C:\\NEW_PATH_FOR_100.exe")
                dialog.table_widget.item(target_row,EditLayoutLinksDialog.COLUMN_URL).setText("")
                dialog.table_widget.cellWidget(target_row,EditLayoutLinksDialog.COLUMN_DUPLICATE).findChild(QCheckBox).setChecked(True)
        dialog.exec_();
        if hasattr(dialog,'accepted')and dialog.accepted and dialog.changes_made:print(f"  Dialog accepted for '{name_to_edit}'.")
        else:print(f"  Dialog cancelled or no changes for '{name_to_edit}'.")
        return dialog
    def _launch_program(self,program_info):mock_orig_pid=program_info.get('mock_orig_pid',int(time.time_ns()%10000));new_pid=mock_orig_pid+5000;print(f"    Simulating launch: '{program_info.get('name')}' (Orig PID {mock_orig_pid})->New PID {new_pid}");return new_pid,mock_orig_pid
    
    def apply_layout_data(self, layout_name_to_apply, active_layout_data):
        print(f"\n--- MainWindow.apply_layout_data for: {layout_name_to_apply} ---")
        if not active_layout_data: print("  No active layout data. Skipping."); return {}

        # This is the conceptual "Pass 1" where decisions about launching are made.
        # It populates windows_to_launch and programs_to_launch_directly.
        windows_to_launch = [] # List of (hwnd_str_from_layout, saved_info_dict)
        programs_to_launch_directly = active_layout_data.get('programs', []) # Standalone programs
        skipped_launch_count = 0
        
        # Simulate finding existing windows. In real app, this would scan open windows.
        # For this test, we'll define which HWNDs from layout are "found" as existing.
        # Keys are hwnd_str from layout, values are the actual HWNDs if found.
        MOCK_EXISTING_HWNDS_MAP = {"100": 10001} # Layout's "100" is found as HWND 10001

        print("  [Pass 1A] Processing windows defined in layout...")
        saved_windows_dict = active_layout_data.get('windows', {})
        for hwnd_str, saved_info in saved_windows_dict.items():
            saved_rect = saved_info.get('rect')
            width = saved_rect[2] - saved_rect[0] if saved_rect and len(saved_rect)==4 else 0
            height = saved_rect[3] - saved_rect[1] if saved_rect and len(saved_rect)==4 else 0
            if width <= 0 or height <= 0: print(f"    Skipping invalid geometry for {hwnd_str}"); continue

            is_placeholder = saved_info.get('is_placeholder', False)
            target_hwnd = None 
            
            if not is_placeholder:
                # Simulate finding an existing window. MOCK_EXISTING_HWNDS_MAP is defined in the test function.
                target_hwnd = getattr(self.apply_layout_data, 'MOCK_EXISTING_HWNDS_MAP', {}).get(hwnd_str)
                if target_hwnd:
                    print(f"    Found existing window for layout HWND_STR {hwnd_str} -> Actual HWND {target_hwnd}. Applying geometry (simulated).")
                    # self.window_manager.apply_geometry(target_hwnd, saved_info) 
                    # handled_existing_hwnds.add(target_hwnd) # This set would be used by later passes
            
            allow_duplicate = saved_info.get('allow_duplicate_launch', False)
            has_launch_info = bool(saved_info.get('launch_path') or saved_info.get('launch_url'))

            if target_hwnd and not is_placeholder: # Existing, non-placeholder window found
                if has_launch_info:
                    if allow_duplicate:
                        print(f"    Existing HWND {target_hwnd} for {hwnd_str}, allow_duplicate=True. Adding to launch list.")
                        windows_to_launch.append((hwnd_str, saved_info))
                    else: # allow_duplicate is False
                        skipped_launch_count += 1
                        print(f"    Existing HWND {target_hwnd} for {hwnd_str}, allow_duplicate=False. Skipping launch. Skipped count: {skipped_launch_count}")
                # If no launch_info, it's just an existing window to be positioned, not re-launched or skipped.
            
            else: # No existing window found, or it's a placeholder
                if has_launch_info:
                    # If it's a placeholder, it should always be "launched" (which might mean creating a dummy).
                    # If not a placeholder but no existing window, it should be launched.
                    print(f"    No existing window for {hwnd_str} (or is placeholder with launch info). Adding to launch list.")
                    windows_to_launch.append((hwnd_str, saved_info))
        
        print(f"  [Pass 1A] Finished. Windows to launch: {len(windows_to_launch)}, Skipped (due to no-duplicate on existing): {skipped_launch_count}")

        # --- Pass 1B: Launching Processes ---
        print("\n  [Pass 1B] Launching processes from 'programs' list and 'windows_to_launch'...")
        self.launched_processes = {} 
        
        # Launch standalone programs from 'programs' list
        for p_info in programs_to_launch_directly: # programs_to_launch_directly was from active_layout_data.get('programs', [])
            actual_pid, layout_key_from_program = self._launch_program(p_info) 
            # layout_key_from_program is typically mock_orig_pid from p_info
            self.launched_processes[layout_key_from_program] = {'pid': actual_pid, 'saved_info': p_info, 'status': 'launched_program'}

        # Launch windows from the windows_to_launch list (populated in Pass 1A)
        for hwnd_str_layout_key, saved_win_info_to_launch in windows_to_launch:
            actual_pid, _ = self._launch_program(saved_win_info_to_launch) # _launch_program uses mock_orig_pid from saved_win_info
            # Key for launched_processes for these windows should be their original hwnd_str from layout,
            # or a unique identifier if hwnd_str isn't guaranteed unique (e.g. for placeholders).
            # The subtask implies hwnd_str is the key used in saved_windows_dict.
            # If saved_win_info_to_launch has 'mock_orig_pid', _launch_program uses it. Otherwise, it generates one.
            # For consistency, we should use the same keying strategy as for standalone programs if possible,
            # or ensure hwnd_str_layout_key is appropriate.
            # Assuming saved_win_info_to_launch contains 'mock_orig_pid' or similar that _launch_program uses.
            key_for_launched = saved_win_info_to_launch.get('mock_orig_pid', hwnd_str_layout_key) # Prioritize mock_orig_pid if present
            
            self.launched_processes[key_for_launched] = {'pid': actual_pid, 'saved_info': saved_win_info_to_launch, 'status': 'launched_window'}
        
        time.sleep(self.settings.get('time_to_wait_for_apps_to_launch_pass_1', 0.01))
        
        # --- Pass 2 & 3 (PID to HWND mapping for newly launched) ---
        # This part remains largely the same, but now operates on self.launched_processes
        # which contains both standalone programs and windows that were launched.
        print("\n  [Pass 2&3 Combined] PID-to-HWND matching for all launched processes...")
        handled_existing_hwnds=set() # Reset or manage this if Pass 2 was more distinct
        time.sleep(self.settings.get('time_to_wait_for_new_windows_pass_3', 0.01))
        _get_details_func = get_window_details_dummy if not PYWIN32_AVAILABLE else get_window_details_real
        newly_found_map_hwnd = {201:{'pid':6000,'title':'App1 Main Window','process_name':'App1.exe','class_name':'Class1','hwnd':201},206:{'pid':6000,'title':'App1 Second Main','process_name':'App1.exe','class_name':'Class1','hwnd':206},203:{'pid':6001,'title':'App2 Window','process_name':'App2.exe','class_name':'Class2','hwnd':203},204:{'pid':6002,'title':'App3 Window','process_name':'App3.exe','class_name':'ActualApp3Class','hwnd':204}} if not PYWIN32_AVAILABLE else {hr:d for hr,_ in get_open_windows()if hr not in handled_existing_hwnds for d in[_get_details_func(hr)]if d and d['pid']is not None}
        pid_to_new_hwnd_map = {}; processed_new_hwnds = set()
        
        print("    [P3.1] Primary Matching (PID+ProcName+Class)")
        for layout_key, launch_data in self.launched_processes.items():
            if not launch_data['status'].startswith('launched'): continue
            actual_pid = launch_data['pid']; saved_pname = launch_data['saved_info'].get('process_name','').lower(); saved_cname = launch_data['saved_info'].get('class_name','N/A')
            if actual_pid in pid_to_new_hwnd_map:
                if launch_data['status']=='launched':launch_data['status']='mapped_by_other_strong';continue
            for hn,nd in newly_found_map_hwnd.items():
                if hn in processed_new_hwnds or hn in handled_existing_hwnds: continue
                if nd.get('pid')==actual_pid and nd.get('process_name','').lower()==saved_pname and nd.get('class_name','N/A')==saved_cname:
                    pid_to_new_hwnd_map[actual_pid]=hn;processed_new_hwnds.add(hn);launch_data['status']='matched_p3_strong';print(f"      [P3S] PID {actual_pid}(Key {layout_key})->HWND {hn}");break
        
        print("    [P3.2] Fallback Matching (PID only)")
        for layout_key, launch_data in self.launched_processes.items():
            if not launch_data['status'].startswith('launched'): continue
            actual_pid = launch_data['pid']
            if actual_pid in pid_to_new_hwnd_map:
                if launch_data['status']=='launched':launch_data['status']='mapped_by_other_pid';continue
            for hn,nd in newly_found_map_hwnd.items():
                if hn in processed_new_hwnds or hn in handled_existing_hwnds: continue
                if nd.get('pid')==actual_pid:
                    pid_to_new_hwnd_map[actual_pid]=hn;processed_new_hwnds.add(hn);launch_data['status']='matched_p3_pid_only';print(f"      [P3P] PID {actual_pid}(Key {layout_key})->HWND {hn}");break
        
        print("\n  Applying geometry to newly matched windows...")
        for actual_pid, hwnd_cfg in pid_to_new_hwnd_map.items():
            cfg = next((ld['saved_info'] for lk,ld in self.launched_processes.items() if ld['pid']==actual_pid and ld['status'] in ['matched_p3_strong','matched_p3_pid_only']),None)
            if cfg: print(f"    Geom for PID {actual_pid} (HWND {hwnd_cfg}) using cfg for: {cfg.get('name')}")
        print("\n--- MainWindow.apply_layout_data complete. ---"); return {'pid_map': pid_to_new_hwnd_map, 'skipped_count': skipped_launch_count, 'launched_procs': self.launched_processes}

# --- Test cases ---
def run_apply_layout_tests_for_duplicate_flag():
    print("\n--- Testing MainWindow.apply_layout_data for allow_duplicate_launch ---")
    main_window = MainWindow()
    main_window.settings['time_to_wait_for_apps_to_launch_pass_1'] = 0.001 # Faster test
    main_window.settings['time_to_wait_for_new_windows_pass_3'] = 0.001

    # Mock existing windows that apply_layout_data might find
    # This is used inside apply_layout_data's MOCK_EXISTING_HWNDS_MAP
    # For this test, let's assume HWND 100 (from layout) is found as actual HWND 10001
    # And HWND 101 (from layout) is found as actual HWND 10002
    
    # Override MOCK_EXISTING_HWNDS_MAP within the test function's scope if possible,
    # or ensure apply_layout_data uses a passed-in map for testability.
    # For now, will rely on the hardcoded map in the provided apply_layout_data.
    # A better way would be to pass this map or mock get_currently_open_real_windows()

    test_layout = {
        "name": "Duplicate Launch Test Layout",
        "windows": {
            "win1_app1_existing_allow_dup": { # Will be "found" as MOCK_EXISTING_HWNDS_MAP["100"] = 10001
                "hwnd_str": "100", # Key used for MOCK_EXISTING_HWNDS_MAP
                "title": "App1 Existing (Allow Dup)", "process_name": "App1.exe", "class_name": "Class1", 
                "launch_path": "app1.exe", "allow_duplicate_launch": True, "mock_orig_pid": 2000,
                "rect": (0,0,100,100)
            },
            "win2_app2_existing_no_dup": { # Will be "found" as MOCK_EXISTING_HWNDS_MAP["101"] = 10002
                "hwnd_str": "101",
                "title": "App2 Existing (No Dup)", "process_name": "App2.exe", "class_name": "Class2", 
                "launch_path": "app2.exe", "allow_duplicate_launch": False, "mock_orig_pid": 2001,
                "rect": (0,0,100,100)
            },
            "win3_app3_not_existing_allow_dup": {
                "hwnd_str": "102", # Not in MOCK_EXISTING_HWNDS_MAP
                "title": "App3 Not Existing (Allow Dup)", "process_name": "App3.exe", "class_name": "Class3", 
                "launch_path": "app3.exe", "allow_duplicate_launch": True, "mock_orig_pid": 2002,
                "rect": (0,0,100,100)
            },
            "win4_app4_existing_no_launch_info": { # Will be "found"
                "hwnd_str": "103", # Add to MOCK_EXISTING_HWNDS_MAP for test
                "title": "App4 Existing (No Launch)", "process_name": "App4.exe", "class_name": "Class4", 
                "allow_duplicate_launch": False, "mock_orig_pid": 2003, # No launch_path/url
                "rect": (0,0,100,100)
            },
             "win5_app5_existing_allow_dup_no_launch_info": {
                "hwnd_str": "104",
                "title": "App5 Existing (Allow Dup, No Launch)", "process_name": "App5.exe", "class_name": "Class5", 
                "allow_duplicate_launch": True, "mock_orig_pid": 2004,
                "rect": (0,0,100,100)
            }
        },
        "programs": [ # Standalone programs to launch
             {"name": "App6 Standalone", "path": "App6.exe", "process_name": "App6.exe", "class_name": "Class6", "mock_orig_pid": 2005}
        ]
    }
    # Adjust MOCK_EXISTING_HWNDS_MAP for this test (ideally this is passed in or mocked)
    main_window.apply_layout_data.MOCK_EXISTING_HWNDS_MAP = {"100": 10001, "101": 10002, "103": 10003, "104":10004}


    results = main_window.apply_layout_data("DuplicateTest", test_layout)
    
    print("\nResults from apply_layout_data for duplicate launch test:")
    print(f"  Skipped launch count: {results.get('skipped_count')}")
    print(f"  Launched processes map (self.launched_processes):")
    for key, data in main_window.launched_processes.items():
        print(f"    LayoutKey/hwnd_str '{key}': ActualPID {data['pid']}, Status: {data['status']}, OrigName: {data['saved_info'].get('title', data['saved_info'].get('name'))}")

    # Assertions
    # win1: existing, allow_dup=True, has_launch -> should be launched. Original mock_orig_pid 2000.
    assert main_window.launched_processes['2000']['status'].startswith('launched'), "win1 should be launched (allow_duplicate)"
    
    # win2: existing, allow_dup=False, has_launch -> should be skipped.
    assert results.get('skipped_count') == 1, "win2 should have incremented skipped_launch_count"
    # Ensure win2 (mock_orig_pid 2001) is NOT in launched_processes or its status reflects it wasn't re-launched
    # The current logic for windows_to_launch means it won't even be in self.launched_processes if skipped *before* _launch_program.
    # The refactor should ensure '2001' is not in launched_processes from the windows_to_launch list.
    # Let's check that it's not in launched_processes keyed by its original identifier if it was skipped.
    # This part needs careful checking of how keys are made for self.launched_processes.
    # The current _launch_program uses mock_orig_pid, so '2001' would be the key if it was launched.
    # If it was skipped, it shouldn't be in self.launched_processes from the windows_to_launch list.
    # The test setup for apply_layout_data now populates self.launched_processes from 'programs' list first,
    # then from 'windows_to_launch'.
    # So, if win2 was skipped, its original_pid_key (2001) for the window entry should not be in self.launched_processes from windows_to_launch.
    # This needs to be verified by checking if a process with original ID '2001' was launched *from the window definition*.
    # The current structure of launched_processes is {layout_key_of_launched_item: data}.
    # If win2 (key "win2_app2_existing_no_dup" or its mock_orig_pid "2001") was skipped, it won't be added from windows_to_launch.
    
    # win3: not existing, has_launch -> should be launched. Original mock_orig_pid 2002.
    assert main_window.launched_processes['2002']['status'].startswith('launched'), "win3 should be launched (not existing)"
    
    # win4: existing, allow_dup=False, no_launch_info -> not added to windows_to_launch, skipped_count not incremented for THIS reason.
    # (skipped_count is only for when a launch is actively skipped due to no-dupe policy)
    # Ensure it's not in launched_processes from windows_to_launch
    
    # win5: existing, allow_dup=True, no_launch_info -> not added to windows_to_launch.
    # Ensure it's not in launched_processes from windows_to_launch

    # App6: standalone program -> should be launched. Original mock_orig_pid 2005.
    assert main_window.launched_processes['2005']['status'] == 'launched_program', "App6 should be launched (standalone program)"

    print("\n--- run_apply_layout_tests_for_duplicate_flag tests complete ---")


if __name__ == '__main__':
    print("--- Running Main Test Suite ---")
    run_edit_layout_links_dialog_refactor_tests() # From previous task
    run_apply_layout_tests_for_duplicate_flag() # New test for this task
    print("\n--- Full Test Suite (selected tests) Complete ---")

[end of windows_utils.py]
