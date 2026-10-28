"""Local Tk owner control panel. No web server and no automatic outbound actions.
All outbound actions open the terminal executor, which requires an exact go ID.
"""
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from concierge_assistant import Store, DEFAULTS, ROOT, local_draft, utc


def launch_args(command, *values):
    return [sys.executable, str(ROOT / 'concierge_assistant.py'), command, *map(str, values)]


def exact_email(address):
    from email.utils import parseaddr
    return bool(address and parseaddr(address)[1] == address and '@' in address
                and not any(c in address for c in '\r\n,;'))


class Panel:
    def __init__(self, window):
        self.window = window
        self.store = Store()
        cfg = self.store.root / 'concierge_config.json'
        if not cfg.exists(): cfg.write_text(json.dumps(DEFAULTS, indent=2), encoding='utf-8')
        self.processes = []
        self.selected_action = None
        self.selected_source = ''
        window.title('Simply Just Task — Dell Concierge (development build)')
        window.geometry('1150x850')
        window.protocol('WM_DELETE_WINDOW', self.close)
        ttk.Label(window, text='NEXTDOOR FIRST | Callback (352) 849-2344 | No unapproved sends',
                  font=('Segoe UI', 13, 'bold')).pack(pady=6)
        ttk.Label(window, text='Not yet live-tested. Monitoring is periodic; phone AI answering is NOT connected.').pack()
        controls = ttk.Frame(window); controls.pack(fill='x', padx=10, pady=6)
        for label, fn in [('Log into Nextdoor', lambda: self.launch('login')),
                          ('Check once', lambda: self.launch('run-once')),
                          ('Start 24h checks', self.watch), ('STOP', self.stop),
                          ('Refresh', self.refresh), ('Open settings', self.settings),
                          ('Read mail', lambda: self.launch('email-scan')),
                          ('Zoho Voice window', lambda: self.launch('phone'))]:
            ttk.Button(controls, text=label, command=fn).pack(side='left', padx=2)
        self.state = tk.StringVar()
        ttk.Label(window, textvariable=self.state).pack(anchor='w', padx=12)
        tabs = ttk.Notebook(window); tabs.pack(fill='both', expand=True, padx=10, pady=6)
        inbox = ttk.Frame(tabs); tabs.add(inbox, text='Observed posts / messages / email')
        actions = ttk.Frame(tabs); tabs.add(actions, text='Drafts / send status')
        self.observations = ttk.Treeview(inbox, columns=('channel','url','time'), show='headings', height=9)
        for key in ('channel','url','time'): self.observations.heading(key, text=key)
        self.observations.column('channel', width=170); self.observations.column('url', width=550)
        self.observations.pack(fill='both', expand=True)
        self.observations.bind('<<TreeviewSelect>>', self.choose_source)
        self.sources = {}
        source_controls = ttk.Frame(inbox); source_controls.pack(fill='x', pady=4)
        ttk.Button(source_controls, text='Use selected source for a new draft', command=self.use_source).pack(side='left')
        ttk.Button(source_controls, text='Export observations CSV (local)', command=self.export).pack(side='left', padx=6)
        ttk.Label(source_controls, text='No automatic Zoho sync. CSV export is local only.').pack(side='left')
        self.source_text = tk.Text(inbox, height=12, wrap='word'); self.source_text.pack(fill='both', expand=True)
        self.actions = ttk.Treeview(actions, columns=('id','channel','kind','recipient','status'), show='headings', height=13)
        for key in ('id','channel','kind','recipient','status'): self.actions.heading(key, text=key)
        self.actions.column('id',width=40); self.actions.column('recipient',width=380)
        self.actions.pack(fill='both', expand=True)
        self.actions.bind('<<TreeviewSelect>>', self.choose_action)
        ttk.Label(actions, text='Draft / uncertain / SMTP accepted / verified browser indicator are different states. Inspect account before retrying.').pack(anchor='w')
        editor = ttk.LabelFrame(window, text='Review exact action — save draft first, then send with terminal confirmation')
        editor.pack(fill='both', padx=10, pady=4)
        self.fields = {}
        for i, (label, initial) in enumerate([('channel','Nextdoor'), ('kind','comment'),
                ('target',''), ('recipient',''), ('subject','')]):
            ttk.Label(editor, text=label).grid(row=i, column=0, sticky='w')
            var = tk.StringVar(value=initial); self.fields[label] = var
            if label == 'kind':
                entry = ttk.Combobox(editor, textvariable=var, values=['comment','post','dm','reply','email'], state='readonly')
            else: entry = ttk.Entry(editor, textvariable=var, width=105)
            entry.grid(row=i, column=1, columnspan=5, sticky='ew', padx=4)
        editor.columnconfigure(1, weight=1)
        self.body = tk.Text(editor, height=5, wrap='word'); self.body.grid(row=5, column=0, columnspan=6, sticky='ew', padx=4)
        for col, (label, fn) in enumerate([('New draft', self.new), ('Save draft', self.save),
                    ('Local AI draft', self.draft_local), ('Review/send saved ID', self.send),
                    ('Remember preference', self.remember), ('Screenshot', lambda: self.launch('desktop','screenshot'))]):
            ttk.Button(editor, text=label, command=fn).grid(row=6, column=col, padx=3, pady=6)
        ttk.Label(window, text='Old main ZIP does not contain this build. No installation, account sends or phone answering performed by chat.').pack(pady=4)
        self.refresh()

    def launch(self, command, *values):
        try:
            if command in ['send','login','phone'] and (self.store.data / 'worker.lock').exists():
                raise RuntimeError('Stop monitoring and close its browser first. If crashed, verify no worker exists before removing stale worker.lock.')
            flags = subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            # No shell, credential arguments or hidden web server.
            proc = subprocess.Popen(launch_args(command, *values), cwd=ROOT, creationflags=flags)
            self.processes.append(proc)
            self.state.set('Opened ' + command + '. Review its console. Nothing is sent without its exact confirmation.')
        except Exception as exc: messagebox.showerror('Cannot start', str(exc))

    def watch(self):
        if (self.store.data / 'worker.lock').exists():
            messagebox.showwarning('Already running / stale lock', 'A worker lock exists. Do not start a second monitor.'); return
        if (self.store.data / 'STOP').exists():
            if not messagebox.askyesno('Resume checks?', 'Clear STOP and start periodic read-only monitoring at all hours?'): return
            (self.store.data / 'STOP').unlink()
        self.launch('watch')

    def stop(self):
        (self.store.data / 'STOP').touch()
        self.store.audit('owner_panel_stop')
        self.state.set('STOP requested. In-flight remote actions cannot be recalled. Allow network timeout for exit.')

    def refresh(self):
        for tree in [self.observations, self.actions]:
            for ident in tree.get_children(): tree.delete(ident)
        self.sources = {}
        for idx, row in enumerate(self.store.db.execute('SELECT * FROM observations ORDER BY created DESC LIMIT 200')):
            item = dict(row); ident = str(idx); self.sources[ident] = item
            self.observations.insert('', 'end', iid=ident, values=(item['channel'],item['url'],item['created']))
        for row in self.store.db.execute('SELECT id,channel,kind,recipient,status FROM actions ORDER BY id DESC LIMIT 200'):
            item = dict(row)
            self.actions.insert('', 'end', iid=str(item['id']), values=tuple(item.values()))
        self.state.set('STOPPED' if (self.store.data / 'STOP').exists() else 'Ready — monitoring only runs when started.')

    def choose_source(self, _=None):
        ids = self.observations.selection()
        if not ids: return
        item = self.sources[ids[0]]
        self.source_text.delete('1.0','end'); self.source_text.insert('1.0',item['text'])

    def use_source(self):
        ids = self.observations.selection()
        if not ids: return
        item = self.sources[ids[0]]
        self.new()
        self.fields['channel'].set(item['channel']); self.fields['target'].set(item['url'])
        self.selected_source = item['text']
        self.source_text.delete('1.0','end'); self.source_text.insert('1.0',item['text'])
        if item['channel'] == 'Zoho Mail':
            self.fields['kind'].set('email')
            try:
                obj = json.loads(item['text'])
                from email.utils import parseaddr
                address = parseaddr(obj['from'])[1]
                self.fields['recipient'].set(address); self.fields['target'].set('mailto:' + address)
                subject = obj.get('subject','')
                self.fields['subject'].set(subject if subject.lower().startswith('re:') else 'Re: ' + subject)
            except (ValueError, KeyError): pass
        self.state.set('Read the full source, then confirm exact recipient and target. Do not use a feed URL as a post permalink.')

    def choose_action(self, _=None):
        ids = self.actions.selection()
        if not ids: return
        item = self.store.action(int(ids[0])); self.selected_action = item['id']
        for key, var in self.fields.items(): var.set(item[key])
        self.selected_source = item['source']
        self.source_text.delete('1.0','end'); self.source_text.insert('1.0',item['source'])
        self.body.delete('1.0','end'); self.body.insert('1.0',item['body'])
        self.state.set('Selected action ' + str(item['id']) + ': ' + item['status'])

    def new(self):
        self.selected_action = None; self.selected_source = ''
        for key, var in self.fields.items(): var.set({'channel':'Nextdoor','kind':'comment'}.get(key,''))
        self.body.delete('1.0','end')
        self.state.set('New draft; no outbound action.')

    def save(self):
        try:
            values = {key: var.get().strip() for key, var in self.fields.items()}
            body = self.body.get('1.0','end-1c')
            if values['kind'] == 'email' and not exact_email(values['recipient']):
                raise ValueError('One exact email recipient required.')
            if not values['target']: raise ValueError('Exact target URL or mailto address required.')
            # Create a new immutable snapshot rather than silently changing a queued recipient.
            ident = self.store.add(values['channel'],values['kind'],values['target'],values['recipient'],
                                    body, self.selected_source, values['subject'])
            self.selected_action = ident; self.refresh(); self.state.set('Saved NEW draft ID ' + str(ident) + '. Nothing sent.')
        except Exception as exc: messagebox.showerror('Draft not saved', str(exc))

    def send(self):
        if self.selected_action is None:
            messagebox.showwarning('Save first', 'Save your draft, then select its ID from Drafts.'); return
        item = self.store.action(self.selected_action)
        live_values = {key: var.get().strip() for key, var in self.fields.items()}
        if any(item[k] != v for k, v in live_values.items()) or item['body'] != self.body.get('1.0','end-1c'):
            messagebox.showwarning('Unsaved edits', 'Save as a new draft before sending edited content.'); return
        self.launch('send', self.selected_action)

    def draft_local(self):
        if not self.selected_source:
            messagebox.showwarning('Select source', 'Select an observed message/post and choose Use selected source.'); return
        try:
            self.state.set('Drafting locally; the panel may wait up to 120 seconds. No send.')
            self.window.update_idletasks()
            text = local_draft(self.store, self.selected_source)
            self.body.delete('1.0','end'); self.body.insert('1.0',text)
            self.state.set('Local AI draft ready. Verify all facts, then save. Nothing sent.')
        except Exception as exc: messagebox.showerror('Local model unavailable', str(exc))

    def remember(self):
        text = simpledialog.askstring('Owner-approved memory', 'Preference to remember (no passwords or safety overrides):')
        if not text or not text.strip(): return
        self.store.db.execute('INSERT INTO memory(text,created) VALUES (?,?)', (text.strip(), utc()))
        self.store.db.commit(); self.store.audit('owner_preference_saved')
        messagebox.showinfo('Remembered', 'Saved locally. This does not retrain a model or change safety rules.')

    def settings(self):
        path = self.store.root / 'concierge_config.json'
        if os.name == 'nt': subprocess.Popen(['notepad.exe', str(path)])
        else: messagebox.showinfo('Configuration file', str(path))

    def export(self):
        path = filedialog.asksaveasfilename(defaultextension='.csv', initialfile='sjt-observations.csv')
        if not path: return
        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f); writer.writerow(['channel','url','text','created'])
            for row in self.store.db.execute('SELECT channel,url,text,created FROM observations ORDER BY created DESC'):
                # Neutralize spreadsheet formulas in untrusted posts/message fields.
                writer.writerow(["'" + str(v) if str(v).lstrip().startswith(('=','+','-','@')) else str(v) for v in row])
        self.store.audit('owner_exported_observations')
        messagebox.showinfo('Saved locally', 'CSV exported. This does not save anything to Zoho automatically. Protect this file: it may contain private messages.')

    def close(self):
        if any(proc.poll() is None for proc in self.processes):
            if messagebox.askyesno('Stop checks before closing?', 'Set STOP so running workers exit after their current operation?'):
                self.stop()
        self.store.db.close(); self.window.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    Panel(root)
    root.mainloop()
