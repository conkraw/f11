"""Exercise full page-render code with a widget stub, NOT a browser test.

The stub records rendered keys/downloads. It does not emulate all Streamlit
lifecycle behaviors and cannot prove browser compatibility.
"""
from pathlib import Path
import sys
import types
from test_callbacks import app,open_room

class Panel:
    def __init__(self, st): self.st=st
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def __getattr__(self,name): return getattr(self.st,name)


def equip(app,monkeypatch):
    st=app.st
    downloads=[]
    keys=set()
    def control(label,*args,**kwargs):
        key=kwargs.get('key')
        options=args[0] if args and isinstance(args[0],(list,tuple)) else None
        default=kwargs.get('value',args[0] if args and isinstance(args[0],str) else '')
        if options:
            default=options[kwargs.get('index',0)]
        if key:
            assert key not in keys, 'Duplicate widget key: '+key
            keys.add(key)
            st.session_state.setdefault(key,default)
            return st.session_state[key]
        return default
    for name in ['text','caption','info','warning','error','success','title','header','subheader','divider','markdown']:
        setattr(st,name,lambda *args,**kwargs:None)
    for name in ['text_input','text_area','selectbox','radio','checkbox']:
        setattr(st,name,control)
    st.expander=lambda *a,**k:Panel(st)
    st.form=lambda *a,**k:Panel(st)
    st.columns=lambda n,*a,**k:[Panel(st) for _ in range(n if isinstance(n,int) else len(n))]
    st.tabs=lambda names:[Panel(st) for _ in names]
    st.button=lambda *a,**k:False
    st.form_submit_button=lambda *a,**k:False
    st.download_button=lambda label,data,*a,**k:downloads.append((label,data))
    st.sidebar=Panel(st)
    comp=types.ModuleType('streamlit.components')
    v1=types.ModuleType('streamlit.components.v1')
    v1.html=lambda *a,**k:None
    comp.v1=v1
    st.components=comp
    monkeypatch.setitem(sys.modules,'streamlit.components',comp)
    monkeypatch.setitem(sys.modules,'streamlit.components.v1',v1)
    return downloads


def test_render_empty_handoff_and_downloads(app,monkeypatch):
    open_room(app)
    downloads=equip(app,monkeypatch)
    app.handoff_page(None)
    assert any(isinstance(data,bytes) and data.startswith(b'%PDF') for _,data in downloads)


def test_render_combined_import_preview(app,monkeypatch):
    open_room(app)
    ss=app.st.session_state
    ss['paste']=(Path(__file__).parents[1]/'examples/synthetic_smartphrase.txt').read_text()
    app.read_sections()
    equip(app,monkeypatch)
    app.handoff_page(None)


def test_render_imported_meds_and_new_pending_same_room(app,monkeypatch):
    open_room(app)
    ss=app.st.session_state
    source=(Path(__file__).parents[1]/'examples/synthetic_smartphrase.txt').read_text()
    ss['paste']=source
    app.read_sections()
    ss['med_import_reviewed']=True
    app.apply_medication_import()
    ss['paste']=source
    app.read_sections()
    equip(app,monkeypatch)
    app.handoff_page(None)


def test_render_admin_empty_and_saved_mapping(app,monkeypatch):
    from medications import upsert_rule
    open_room(app)
    app.st.session_state['vault']['settings']['medication_mappings']=upsert_rule([],'acetaminophen','Neurologic')
    equip(app,monkeypatch)
    app.admin_page(None)


def test_session_upgrade_preserves_unsaved_notes(app):
    from test_medications import legacy_vault
    from copy import deepcopy
    old=legacy_vault()
    ss=app.st.session_state
    ss.update(vault=old,drafts={'P4102':deepcopy(old['rooms']['P4102'])},base_sheets={'P4102':deepcopy(old['rooms']['P4102'])})
    ss['drafts']['P4102']['fields']['Respiratory']='Unsaved old draft'
    app.upgrade_existing_session()
    assert ss['vault']['schema']==2
    assert ss['drafts']['P4102']['fields']['Respiratory']=='Unsaved old draft'
    assert ss['base_sheets']['P4102']['fields']['Respiratory']==''
    assert ss['drafts']['P4102']['medications']==[]
