# PICU Handoff 6.42

Respiratory medication groups, a linked theophylline result, and editable
categories/subcategories. Built from Version 6.41.

Read DYNAMIC_CATEGORIES_UPDATE.md for the new defaults, mapping priority,
category management, and installation steps.

## Upgrade an existing deployment

Upload the contents of this folder to the existing application code directory.
Keep app.py at the root. Include categories.py and category_ui.py. Restart the
application, then refresh the browser.

Keep your existing private Secrets, both passwords, encryption key, shared data
archive, and BMI reference CSV unchanged. Do not run the setup generators during
an upgrade. There are no new Python dependencies. Old handoffs upgrade to schema
27 automatically. Do not downgrade after saving with this version.

## Routine use

Choose the room, paste the patient's generated Epic SmartPhrase, and click Create /
update handoff. Review imported information, edit notes and medication placement,
and save. The Instructions / SmartPhrase workspace contains the team's published
SmartPhrase and instructions. An import warning must be reviewed in the app even
though warnings do not print on the handoff.

Under Medications, select one Category for order. It can be a category alone or a
category and one subcategory. That destination is remembered. Source order
fields, hidden-medication settings and infusion rate formatting remain intact.

Admin / Medication categories and subcategories creates, renames, moves and
reorders categories. Admin / Assign medications to categories creates generic
prefix or exact-formulation rules. It works even when no handoff is open and
requires the existing separate Admin password.

Theophylline is shown immediately below a visible aminophylline order, once. If
there is no visible aminophylline order, an eligible result remains in Respiratory.
The existing 24-hour filter remains unchanged.

## Validation and limits

TEST_REPORT.md records local automated testing and preview checks. No live Epic,
shared-storage connection or deployed Streamlit app was tested or changed.
Category labels are local display choices, not an indication determination or
medication recommendation. Review source values before using a handoff.

For a new deployment, the existing START_HERE.html, ADMIN_SETUP.txt and
secrets.example.toml cover installation and access configuration. They are not
steps to repeat when upgrading an existing deployment.
