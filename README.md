# PICU Handoff 6.23: auto-fit printing and clear all

This is the complete app update. Start with PRINT_RESET_UPDATE.md.

- PDF preflight reports the rendered page count for every selected room.
- The default target is one page, with a two-page target available.
- Tighter spacing and bounded column widths help crowded handoffs fit, without clipping data.
- Admin has a one-click shared reset that clears handoffs and deletes custom rooms.
- Medication rules, hidden choices, instructions, SmartPhrase, passwords and error reports are preserved.

Upload the full folder contents with app.py at the root. Preserve all existing Secrets. No new dependencies. Installing the update does not clear data. Schema 18 adds a reset generation to protect against old drafts being restored after a shared reset.

# Earlier setup reference: the user guide and protected Admin

Complete ZIP update based on 6.21. No direct repository changes are made.

## Update an existing deployment

Save open work. Extract PICU622.zip and open PICU_Handoff_v6_22_User_Guide.
Copy all application contents into the current code repository, replacing
matching files. Keep app.py at the root. Keep all current Secrets, encryption
key, app-password hash, GitHub token, medication settings and private data
repository. Do not run create_secrets.py or Generate_Secrets.ipynb again.

No new dependencies or clinical archive schema changes are required. Room
records, save timestamps and every clinical parser keep their previous format.
The sidebar reads: Version 6.22 | User guide and protected Admin.

## Set the second password once

Read ADMIN_SETUP.txt. Run Generate_Admin_Password.ipynb in local JupyterLab, or
run python set_admin_password.py locally. The helper prints exactly one new
admin_password_hash setting, without writing a file or generating an encryption
key. Add the generated line to your existing [app] section in deployment Secrets.
Choose a password different from the app login. Keep the output private.

Admin stays locked until this setting is configured. Routine Handoff, Print all,
Instructions / SmartPhrase and Import errors continue to use the normal app login.
The second password is not individual identity or multifactor authentication.

## Publish team instructions and the Epic source

Open Admin and unlock it with the second password. At the top, edit User
instructions and Epic SmartPhrase. Fill in the exact Epic name/shortcut, the
actual reusable source definition, optional local Epic setup notes, and the
learner guide. Click Save instructions and SmartPhrase.

Only the teaching guide is prefilled. The supplied samples were expanded patient
results, not the actual reusable SmartLinks, so the name and source deliberately
start empty. SMARTPHRASE_TEMPLATE.txt remains a placeholder scaffold. Do not
publish patient results as a reusable source template.

Saving here does not install or change the phrase in Epic. Test a changed source
using your local Epic workflow and synthetic information before using it.

## What users see

Instructions / SmartPhrase in the sidebar provides the eight-step guide and a
read-only source block with copy support and a text download. It also provides
HTML and text downloads of the guide. Handoff has a collapsed Instructions and
Epic SmartPhrase panel above the room selector. No example-loading buttons return.

The steps are: open/sign in, choose Handoff, choose the correct room, run the
phrase in Epic, paste generated text, create/update, review/preview, and save.
The guide also explains new room occupants, partial-section updates, errors,
saved timestamps, shared-session conflicts and Print all.

## Admin access

The whole Admin workspace and its write callbacks recheck the separate unlock.
It expires on leaving Admin, Lock Admin, logout, 15 minutes without Admin activity,
or one hour after unlocking. Changed password hashes revoke a grant on its next
check. There is a per-session password-attempt delay. An expired or absent grant
cannot publish guide text, change Admin mappings/settings, or activate Admin
restore/remove callbacks.

Existing medication mapping, hiding and custom-room controls within Handoff
remain available with the app login, as requested in the earlier workflow. This
is an Admin-screen gate, not a new per-user role/permissions system.

## Separate encrypted content

The guide is stored at encrypted-data/user-guide.enc in the same existing private
data repository, with the same encryption key. It contains reusable teaching
content only. It does not contain the Admin password, app password, or hashes.
Guide publishing does not rewrite handoff-v1.enc, room timestamps, error reports
or medication rules. Ordinary users may refresh the guide independently.

A stale guide save is refused using its expected GitHub file version. The local
editor draft remains available for comparison. Refreshing the read-only guide
does not silently rebase an unsaved Admin draft. Reload published guide into
editor explicitly replaces that draft. A failed read or write does not claim a
publish or change handoffs. Session-only mode is labeled and is not persistent.

Existing encryption and app login do not establish clinical approval. A room
number does not make clinical text anonymous. The existing hosting, access,
retention, and data-handling requirements remain. No live repository was used
while building this update.

## Tests and files

Read TEST_REPORT.md for exact checks and limitations. New modules: user_guide.py,
guide_store.py and admin_access.py. New setup helper: set_admin_password.py and
Generate_Admin_Password.ipynb. USER_GUIDE.html and USER_INSTRUCTIONS.txt are
standalone copies of the default learner guide.
