// Quillmail: a minimal mail clone for cross-app tasks. Fresh state per boot (seed.json copied into a temp dir),
// persisted to state.json after every write so a verifier can read backend state. Serves only index.html + /api.
import http from 'node:http';
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.MAIL_PORT || 5180);
const CLOCK = Date.parse(process.env.CLOCK_FIXED_TIME || '2026-09-15T14:00:00Z');
const started = Date.now();
const nowIso = () => new Date(CLOCK + (Date.now() - started)).toISOString();
const dir = mkdtempSync(join(tmpdir(), 'quillmail-'));
const STATE = join(dir, 'state.json');
const seed = JSON.parse(readFileSync(join(root, process.env.MAIL_SEED || 'seed.json'), 'utf8'));
const state = { me: seed.me, messages: seed.messages.map((m) => ({ ...m, from: m.from_, from_: undefined })) };
let seq = 0;
const save = () => writeFileSync(STATE, JSON.stringify(state, null, 1));
save();
console.log(`[mail] state: ${STATE}`);
const PAGE = 10;
const html = readFileSync(join(root, 'index.html'));

function send(res, status, body) {
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
  res.end(JSON.stringify(body));
}
async function body(req) {
  const c = []; for await (const x of req) c.push(x);
  try { return c.length ? JSON.parse(Buffer.concat(c).toString('utf8')) : {}; } catch { return {}; }
}
const lite = ({ body: b, ...m }) => ({ ...m, snippet: b.replace(/\s+/g, ' ').slice(0, 90) });

http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  const p = url.pathname;
  if (p === '/health') return send(res, 200, { ok: true });
  if (req.method === 'GET' && (p === '/' || p === '/index.html' || p.startsWith('/mail'))) {
    res.writeHead(200, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' }); return res.end(html);
  }
  if (!p.startsWith('/api/')) return send(res, 404, { error: 'Not found' });
  if (req.method === 'GET' && p === '/api/now') return send(res, 200, { now: nowIso() });
  if (req.method === 'GET' && p === '/api/folders') {
    const c = (f) => state.messages.filter((m) => m.folder === f);
    return send(res, 200, { inbox: { total: c('inbox').length, unread: c('inbox').filter((m) => !m.read).length }, starred: { total: state.messages.filter((m) => m.starred && m.folder !== 'trash').length }, sent: { total: c('sent').length }, archive: { total: c('archive').length } });
  }
  if (req.method === 'GET' && p === '/api/messages') {
    const folder = url.searchParams.get('folder') || 'inbox';
    const q = (url.searchParams.get('q') || '').trim().toLowerCase();
    let list = folder === 'starred' ? state.messages.filter((m) => m.starred) : state.messages.filter((m) => m.folder === folder);
    if (q) list = list.filter((m) => [m.fromName, m.from, m.to, m.subject, m.body].join(' ').toLowerCase().includes(q));
    list = [...list].sort((a, b) => b.date.localeCompare(a.date));
    const pages = Math.max(1, Math.ceil(list.length / PAGE));
    const page = Math.min(Math.max(1, Number(url.searchParams.get('page') || 1)), pages);
    return send(res, 200, { items: list.slice((page - 1) * PAGE, page * PAGE).map(lite), page, pages, total: list.length, pageSize: PAGE });
  }
  const m = p.match(/^\/api\/messages\/([\w-]+)(?:\/(\w+))?$/);
  if (!m) return send(res, 404, { error: 'Not found' });
  const msg = state.messages.find((x) => x.id === m[1]);
  if (!msg) return send(res, 404, { error: 'Message not found' });
  const act = m[2];
  if (req.method === 'GET' && !act) { if (!msg.read) { msg.read = true; save(); } return send(res, 200, msg); }
  if (req.method !== 'POST') return send(res, 405, { error: 'Method not allowed' });
  const b = await body(req);
  if (act === 'archive') msg.folder = 'archive';
  else if (act === 'inbox') msg.folder = 'inbox';
  else if (act === 'read') msg.read = b.read !== false;
  else if (act === 'star') msg.starred = b.starred !== undefined ? !!b.starred : !msg.starred;
  else if (act === 'reply') {
    if (!b.body || !String(b.body).trim()) return send(res, 400, { error: 'Reply body required' });
    const r = { id: `s${String(++seq).padStart(2, '0')}`, fromName: state.me.name, from: state.me.address, to: msg.from, subject: msg.subject.startsWith('Re: ') ? msg.subject : `Re: ${msg.subject}`, body: String(b.body), date: nowIso(), folder: 'sent', read: true, starred: false, inReplyTo: msg.id };
    state.messages.push(r); save(); return send(res, 201, r);
  } else return send(res, 404, { error: 'Unknown action' });
  save(); return send(res, 200, msg);
}).listen(PORT, '127.0.0.1', () => console.log(`[mail] listening on http://127.0.0.1:${PORT}`));
