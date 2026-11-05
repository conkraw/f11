from copy import deepcopy
from pathlib import Path
from test_callbacks import app,open_room
from medications import upsert_rule

SAMPLE=Path(__file__).parents[1]/'examples'/'synthetic_smartphrase.txt'


def read(app):
    open_room(app)
    app.st.session_state['paste']=SAMPLE.read_text()
    app.read_sections()


def apply(app):
    ss=app.st.session_state
    ss['med_import_reviewed']=True
    ss['med_replace_confirm']=True
    app.apply_medication_import()


def test_combined_read_diagnoses_and_meds(app):
    read(app)
    ss=app.st.session_state
    assert not ss['pending']['error']
    assert len(ss['medication_pending']['rows'])==9


def test_apply_diagnoses_keeps_medication_preview(app):
    read(app)
    app.apply_import()
    ss=app.st.session_state
    assert len(ss['medication_pending']['rows'])==9
    assert 'Synthetic practice diagnosis' in ss['drafts']['P4102']['fields']['Diagnoses']
    apply(app)
    assert len(ss['drafts']['P4102']['medications'])==9
    assert ss['paste']==''


def test_apply_meds_first_keeps_diagnosis_preview(app):
    read(app)
    apply(app)
    ss=app.st.session_state
    assert ss['pending']['text']
    app.apply_import()
    assert len(ss['drafts']['P4102']['medications'])==9
    assert ss['drafts']['P4102']['fields']['Diagnoses']
    assert ss['paste']==''


def test_medication_import_does_not_save_until_clicked(app):
    read(app)
    apply(app)
    ss=app.st.session_state
    assert not ss['vault']['rooms']
    ss['reviewed']=True
    app.save_room(None)
    assert len(ss['vault']['rooms']['P4102']['medications'])==9
    assert 'Example Clinician' not in str(ss['vault'])


def test_import_requires_medication_review(app):
    read(app)
    app.apply_medication_import()
    assert not app.st.session_state['drafts']['P4102']['medications']


def test_import_replace_requires_confirmation(app):
    read(app)
    apply(app)
    ss=app.st.session_state
    previous=deepcopy(ss['drafts']['P4102']['medications'])
    ss['paste']=SAMPLE.read_text()
    app.read_sections()
    ss['med_import_reviewed']=True
    app.apply_medication_import()
    assert ss['drafts']['P4102']['medications']==previous
    ss['med_replace_confirm']=True
    app.apply_medication_import()
    assert len(ss['drafts']['P4102']['medications'])==9
    assert ss['drafts']['P4102']['medications']!=previous


def test_switch_rooms_clears_medication_preview(app):
    read(app)
    open_room(app,'P4104')
    assert 'medication_pending' not in app.st.session_state
    assert app.st.session_state['paste']==''


def test_remap_current_draft_and_pending_only(app):
    read(app)
    apply(app)
    ss=app.st.session_state
    ss['reviewed']=True
    app.save_room(None)
    before=deepcopy(ss['vault']['rooms']['P4102'])
    ss['vault']['settings']['medication_mappings']=upsert_rule([],'acetaminophen','Neurologic')
    app.reapply_current_mappings()
    assert ss['drafts']['P4102']['medications'][0]['section']=='Neurologic'
    assert ss['vault']['rooms']['P4102']==before
    assert not ss['reviewed']


def test_new_patient_clears_medications(app):
    read(app)
    apply(app)
    ss=app.st.session_state
    ss['confirm_new']=True
    app.start_new_patient()
    assert not ss['drafts']['P4102']['medications']
    assert 'medication_pending' not in ss


def test_bad_medication_block_cannot_partially_apply(app):
    read(app)
    ss=app.st.session_state
    ss['paste']='bbbbbbbb\nMedications:\n• med\t1 mg\tIV\tq4h\n• no tabs here\nbbbbbbbb'
    app.read_medications()
    ss['med_import_reviewed']=True
    app.apply_medication_import()
    assert not ss['drafts']['P4102']['medications']


def test_b_only_paste_imports_without_diagnosis(app):
    read(app)
    ss=app.st.session_state
    ss['paste']='bbbbbbbb\nMedications:\n• med\t1 mg\tIV\tq4h\nbbbbbbbb'
    app.read_sections()
    assert ss['pending']['error'] and not ss['medication_pending']['error']
    apply(app)
    assert len(ss['drafts']['P4102']['medications'])==1


def test_medication_edit_marks_draft_unreviewed(app):
    read(app)
    apply(app)
    ss=app.st.session_state
    row=ss['drafts']['P4102']['medications'][0]
    ss['edit_test']='Changed route'
    ss['reviewed']=True
    app.medication_row_change('draft','P4102',row['id'],'route','edit_test')
    assert row['route']=='Changed route' and not ss['reviewed']
