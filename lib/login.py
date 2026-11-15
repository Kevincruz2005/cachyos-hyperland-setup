# SPDX-License-Identifier: MIT
"""Pure, conservative login transformations. This module never writes live files."""
import json
import re
import tomllib

GREETER_VERSIONS = ('1.6.0', '1.7.0')
GREETD_VERSIONS = ('0.10.3',)


def greetd_config(text, username):
    if not re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_-]*', username):
        raise RuntimeError('Unsupported login username.')
    data = tomllib.loads(text)
    if set(data) - {'terminal', 'default_session'}:
        raise RuntimeError('Custom greetd sections/autologin require manual review.')
    terminal = data.get('terminal', {})
    if set(terminal) != {'vt'} or type(terminal['vt']) is not int or not 1 <= terminal['vt'] <= 63:
        raise RuntimeError('Custom greetd terminal needs review.')
    session = data.get('default_session', {})
    if set(session) != {'command', 'user'} or session['user'] != 'greeter':
        raise RuntimeError('Custom greetd session user/configuration needs review.')
    command = session['command']
    wanted = '/usr/bin/noctalia-greeter-session -- --session hyprland-uwsm --user ' + username
    if command not in ('agreety --cmd /bin/sh', '/usr/bin/agreety --cmd /bin/sh',
                       '/usr/bin/noctalia-greeter-session', wanted):
        raise RuntimeError('Custom greetd launcher must not be silently replaced.')
    return ('[terminal]\nvt = ' + str(terminal['vt']) + '\n\n[default_session]\ncommand = '
            + json.dumps(wanted) + '\nuser = "greeter"\n').encode()


def pam_keyring(text, kind):
    """Insert optional hooks only after known includes; never replace auth rules."""
    if kind not in ('greetd', 'passwd'):
        raise ValueError('Unknown PAM target')
    if '\r' in text or '\x00' in text or len(text) > 65536:
        raise RuntimeError('Unsupported PAM file format.')
    # Merely retaining text is insufficient: inserting a line into a stack with
    # custom numeric jump controls could change authentication semantics.
    baseline = ([['auth', 'required', 'pam_securetty.so'],
                 ['auth', 'requisite', 'pam_nologin.so'],
                 ['auth', 'include', 'system-local-login'],
                 ['account', 'include', 'system-local-login'],
                 ['session', 'include', 'system-local-login']]
                if kind == 'greetd' else
                [['auth', 'include', 'system-auth'], ['account', 'include', 'system-auth'],
                 ['password', 'include', 'system-auth']])
    existing_rules = [line.split() for line in text.splitlines()
                      if line.strip() and not line.lstrip().startswith('#')
                      and 'pam_gnome_keyring.so' not in line]
    if existing_rules != baseline:
        raise RuntimeError('Custom PAM rules/control flow require manual review.')
    additions = ([('auth', 'system-local-login', '-auth      optional     pam_gnome_keyring.so'),
                  ('session', 'system-local-login', '-session   optional     pam_gnome_keyring.so auto_start')]
                 if kind == 'greetd' else
                 [('password', 'system-auth', '-password   optional    pam_gnome_keyring.so use_authtok')])
    lines = text.splitlines(keepends=True)
    for stack, include, hook in additions:
        anchor = re.compile(r'^\s*' + stack + r'\s+include\s+' + re.escape(include) + r'\s*$')
        indexes = [i for i, line in enumerate(lines) if anchor.fullmatch(line.rstrip('\n'))]
        if len(indexes) != 1:
            raise RuntimeError('Unknown PAM include layout; existing checks are not changed.')
        existing = [line for line in lines if re.match(r'^\s*-?' + stack + r'\s+.*pam_gnome_keyring\.so\b', line)]
        if existing:
            if len(existing) != 1 or existing[0].split() != hook.split():
                raise RuntimeError('Existing keyring hook differs; review manually.')
            continue
        i = indexes[0]
        if not lines[i].endswith('\n'):
            lines[i] += '\n'
        lines.insert(i + 1, hook + '\n')
    return ''.join(lines).encode()


def editor_argv(text):
    """Merge one root JSONC property, retaining comments and other bytes."""
    if len(text) > 1024 * 1024 or '\x00' in text:
        raise RuntimeError('Invalid editor runtime configuration.')
    # Replace comments with equal-length whitespace so token offsets stay exact.
    clean = list(text)
    i = 0
    while i < len(text):
        if text[i] == '"':
            i += 1
            while i < len(text):
                if text[i] == '\\':
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
        elif text.startswith('//', i) or text.startswith('/*', i):
            end = text.find('\n', i) if text.startswith('//', i) else text.find('*/', i + 2)
            if end == -1:
                if text.startswith('/*', i):
                    raise RuntimeError('Unterminated JSONC comment.')
                end = len(text)
            elif text.startswith('/*', i):
                end += 2
            for j in range(i, end):
                if text[j] != '\n':
                    clean[j] = ' '
            i = end
        else:
            i += 1
    cleaned = ''.join(clean)
    tokens = list(re.finditer(r'"(?:[^"\\]|\\.)*"|[{}\[\]:,]|[^\s{}\[\]:,]+', cleaned))
    # JSONC permits trailing commas; remove only comma tokens before a closing token.
    for a, b in zip(tokens, tokens[1:]):
        if a.group() == ',' and b.group() in ('}', ']'):
            clean[a.start()] = ' '
    original = json.loads(''.join(clean))
    if not isinstance(original, dict):
        raise RuntimeError('Editor runtime configuration is not an object.')
    depth, found = 0, []
    for index, token in enumerate(tokens):
        value = token.group()
        if depth == 1 and value.startswith('"') and json.loads(value) == 'password-store':
            if index + 2 < len(tokens) and tokens[index + 1].group() == ':':
                found.append(tokens[index + 2])
        if value in ('{', '['):
            depth += 1
        elif value in ('}', ']'):
            depth -= 1
    if len(found) > 1:
        raise RuntimeError('Duplicate editor password-store property; review manually.')
    if found:
        token = found[0]
        if not token.group().startswith('"'):
            raise RuntimeError('Unexpected editor password-store value.')
        return (text[:token.start()] + '"gnome-libsecret"' + text[token.end():]).encode()
    opening = next((t for t in tokens if t.group() == '{'), None)
    if opening is None:
        raise RuntimeError('Missing editor runtime object.')
    insertion = '\n    "password-store": "gnome-libsecret"' + (',' if original else '') + '\n'
    return (text[:opening.end()] + insertion + text[opening.end():]).encode()
