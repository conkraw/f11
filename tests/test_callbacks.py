"""Callback tests use a minimal Streamlit stub, NOT a real browser/UI test."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import types
import time
import pytest
from models import new_vault, new_sheet, save_sheet_in


@pytest.fixture
def app(monkeypatch):
    stub=types.ModuleType('streamlit')
    stub.session_state={}
    stub.set_page_config=lambda **kwargs: None
    stub.fragment=lambda **kwargs: (lambda function:function)
    monkeypatch.setitem(sys.modules,'streamlit',stub)
    path=Path(__file__).parents[1]/'app.py'
    spec=importlib.util.spec_from_file_location('app_under_test',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    stub.session_state.update(vault=new_vault(),vault_sha=None,drafts={},base_sheets={},authenticated=True,last_activity=time.monotonic(),login_at=time.monotonic())
    return module


def open_room(app,room='P4102'):
    app.st.session_state['room_choice']=room
    app.open_room()


def test_room_selection_separate_drafts(app):
    open_room(app)
    ss=app.st.session_state
    ss['drafts']['P4102']['fields']['Diagnoses']='First room example'
    open_room(app,'P4104')
    assert ss['drafts']['P4104']['fields']['Diagnoses']==''
    open_room(app)
    assert ss['drafts']['P4102']['fields']['Diagnoses']=='First room example'


def test_read_then_apply_does_not_save_raw_source(app):
    open_room(app)
    ss=app.st.session_state
    ss['paste']='aaaaaaaa\nDiagnoses:\n1. Example\naaaaaaaa\nbbbbbbbb\nMedications:\nRAW_NOT_SAVED\nbbbbbbbb'
    app.read_diagnoses()
    assert ss['diagnosis_preview']=='Example'
    app.apply_import()
    assert ss['drafts']['P4102']['fields']['Diagnoses']=='Example'
    assert ss['paste']==''
    assert ss['vault']['rooms']=={}
    ss['reviewed']=True
    app.save_room(None)
    assert 'RAW_NOT_SAVED' not in str(ss['vault'])


def test_replace_requires_explicit_confirmation(app):
    open_room(app)
    ss=app.st.session_state
    ss['drafts']['P4102']['fields']['Diagnoses']='Existing'
    ss['paste']='aaaaaaaa\nDiagnoses:\n1. New\naaaaaaaa'
    app.read_diagnoses()
    app.apply_import()
    assert ss['drafts']['P4102']['fields']['Diagnoses']=='Existing'
    ss['replace_confirm']=True
    app.apply_import()
    assert ss['drafts']['P4102']['fields']['Diagnoses']=='New'


def test_room_switch_clears_pending_import_and_paste(app):
    open_room(app)
    app.st.session_state['paste']='aaaaaaaa\nDiagnoses:\n1. Example\naaaaaaaa'
    app.read_diagnoses()
    open_room(app,'P4104')
    assert 'pending' not in app.st.session_state
    assert app.st.session_state['paste']==''


def test_new_patient_does_not_save_until_clicked(app):
    open_room(app)
    ss=app.st.session_state
    ss['reviewed']=True
    app.save_room(None)
    old=deepcopy(ss['vault']['rooms']['P4102'])
    ss['confirm_new']=True
    app.start_new_patient()
    assert ss['drafts']['P4102']['id']!=old['id']
    assert ss['vault']['rooms']['P4102']==old


def test_save_requires_review(app):
    open_room(app)
    app.save_room(None)
    assert not app.st.session_state['vault']['rooms']


def test_stale_room_cannot_overwrite_after_reload(app):
    open_room(app)
    ss=app.st.session_state
    newer=new_sheet('P4102')
    newer['fields']['Diagnoses']='Newer saved example'
    ss['vault']=save_sheet_in(ss['vault'],newer)
    ss['reviewed']=True
    app.save_room(None)
    assert ss['vault']['rooms']['P4102']['fields']['Diagnoses']=='Newer saved example'
    assert ss['notice'][0]=='error'


def test_logout_clears_data(app):
    open_room(app)
    app.clear_session()
    assert app.st.session_state=={}


def test_expired_callback_cannot_save(app):
    open_room(app)
    ss=app.st.session_state
    ss['reviewed']=True
    ss['last_activity']=time.monotonic()-1000
    class MustNotSave:
        def save(self,*args):
            raise AssertionError('Expired sessions must not write')
    app.save_room(MustNotSave())
    assert app.st.session_state=={}


def test_edited_preview_survives_widget_cleanup(app):
    open_room(app)
    ss=app.st.session_state
    ss['paste']='aaaaaaaa\nDiagnoses:\n1. Example\naaaaaaaa'
    app.read_diagnoses()
    ss['diagnosis_preview']='Clinician edited example'
    app.update_diagnosis_preview()
    ss.pop('diagnosis_preview')
    assert ss['pending']['text']=='Clinician edited example'
