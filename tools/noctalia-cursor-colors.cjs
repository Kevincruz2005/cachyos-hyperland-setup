#!/usr/bin/env node
// SPDX-License-Identifier: MIT
// One-shot JSONC merge. No extension, watcher, login change or network request.
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');

function parser() {
    for (const file of [
        '/usr/share/cursor/resources/app/node_modules/jsonc-parser/lib/umd/main.js',
        '/usr/share/code/resources/app/node_modules/jsonc-parser/lib/umd/main.js',
    ]) {
        if (fs.existsSync(file)) return require(file);
    }
    throw new Error('Installed JSONC parser unavailable; settings left unchanged.');
}

function regularFile(file, limit, missing = false) {
    for (let part = path.resolve(file); ; part = path.dirname(part)) {
        if (fs.existsSync(part) && fs.lstatSync(part).isSymbolicLink()) {
            throw new Error('Symlink requires manual review; no changes made.');
        }
        if (part === path.dirname(part)) break;
    }
    try {
        const stat = fs.lstatSync(file);
        if (!stat.isFile() || stat.size > limit) throw new Error('Invalid or oversized theme input.');
        return fs.readFileSync(file, 'utf8');
    } catch (error) {
        if (missing && error.code === 'ENOENT') return '{}\n';
        throw error;
    }
}

function objectKeysUnique(node) {
    if (!node || node.type !== 'object') throw new Error('Expected a settings object.');
    const keys = node.children.map(p => p.children[0].value);
    if (new Set(keys).size !== keys.length) throw new Error('Duplicate settings keys require manual review.');
}

function mergeSettings(original, colors, jsonc = parser()) {
    if (!colors || Array.isArray(colors) || typeof colors !== 'object' ||
        Object.keys(colors).length < 1 || Object.keys(colors).length > 100) {
        throw new Error('Invalid color overrides.');
    }
    for (const [key, value] of Object.entries(colors)) {
        if (!/^[A-Za-z][A-Za-z0-9.]+$/.test(key) ||
            typeof value !== 'string' || !/^#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$/.test(value)) {
            throw new Error('Only safe color identifiers and hex values are accepted.');
        }
    }
    const errors = [];
    const options = {allowTrailingComma: true};
    const root = jsonc.parseTree(original, errors, options);
    if (errors.length) throw new Error('Invalid JSONC; settings left unchanged.');
    objectKeysUnique(root);
    const existing = jsonc.findNodeAtLocation(root, ['workbench.colorCustomizations']);
    if (existing) {
        objectKeysUnique(existing);
        // Theme-specific overrides can hide the shared palette. Never erase them.
        for (const item of existing.children) {
            if (item.children[0].value.startsWith('[')) {
                throw new Error('Theme-specific colors require manual merge.');
            }
        }
    }
    let result = original;
    for (const [key, value] of Object.entries(colors)) {
        result = jsonc.applyEdits(result, jsonc.modify(result,
            ['workbench.colorCustomizations', key], value,
            {formattingOptions: {insertSpaces: true, tabSize: 4}}));
    }
    return result;
}

function applyColors(paletteFile, settingsFile) {
    const colors = JSON.parse(regularFile(paletteFile, 16384));
    // Do not create an editor profile on a machine that does not have Cursor.
    const original = regularFile(settingsFile, 1024 * 1024);
    const result = mergeSettings(original, colors);
    if (result === original) return false;
    const temp = path.join(path.dirname(settingsFile), '.noctalia-colors-' + crypto.randomUUID());
    let fd;
    try {
        fd = fs.openSync(temp, 'wx', fs.statSync(settingsFile).mode & 0o777);
        fs.writeFileSync(fd, result);
        fs.fsyncSync(fd);
        fs.closeSync(fd);
        fd = undefined;
        if (regularFile(settingsFile, 1024 * 1024) !== original) {
            throw new Error('Concurrent settings edit detected; retry on the next theme change.');
        }
        fs.renameSync(temp, settingsFile);
    } finally {
        if (fd !== undefined) fs.closeSync(fd);
        if (fs.existsSync(temp)) fs.unlinkSync(temp);
    }
    return true;
}

if (require.main === module) {
    const config = process.env.XDG_CONFIG_HOME || path.join(os.homedir(), '.config');
    const palette = process.argv[2] || path.join(config, 'noctalia/cursor-colors.json');
    const settings = process.argv[3] || path.join(config, 'Cursor/User/settings.json');
    try { applyColors(palette, settings); }
    catch (error) { console.error('Noctalia Cursor colors: ' + error.message); process.exitCode = 1; }
}
module.exports = {mergeSettings, applyColors};
