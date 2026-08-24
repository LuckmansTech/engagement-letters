/* Cloudflare Pages middleware: password gate at the edge.
 *
 * Runs before any static file is served, so an unauthenticated request never
 * receives app.js. This is the difference between a real gate and a check
 * inside the bundle, which anyone could read or skip.
 *
 * Two scopes, so the admin build can carry its own password:
 *   /admin/*   ADMIN_PASSWORD   Templates and Firm editors
 *   everything SITE_PASSWORD    the Letter tool
 *
 * Set SITE_PASSWORD, ADMIN_PASSWORD and SESSION_SECRET as environment
 * variables in the Pages project (Settings, Environment variables). They are
 * never sent to the browser. SESSION_SECRET should be a long random string;
 * changing it signs every existing session out.
 */
const MAX_AGE = 60 * 60 * 12; // 12 hours

const enc = new TextEncoder();

async function sign(value, secret) {
  const key = await crypto.subtle.importKey(
    "raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(value));
  return [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

/* length-independent comparison, so timing does not leak the password */
function same(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

async function makeCookie(scope, secret) {
  const exp = Math.floor(Date.now() / 1000) + MAX_AGE;
  const body = scope + "." + exp;
  return body + "." + (await sign(body, secret));
}

async function cookieValid(raw, scope, secret) {
  if (!raw) return false;
  const parts = raw.split(".");
  if (parts.length !== 3) return false;
  const [got, exp, sig] = parts;
  if (got !== scope) return false;
  if (!/^\d+$/.test(exp) || Number(exp) < Math.floor(Date.now() / 1000)) return false;
  return same(sig, await sign(got + "." + exp, secret));
}

function readCookie(req, name) {
  const raw = req.headers.get("Cookie") || "";
  for (const part of raw.split(";")) {
    const [k, ...v] = part.trim().split("=");
    if (k === name) return v.join("=");
  }
  return null;
}

function loginPage(scope, message) {
  const label = scope === "admin" ? "Administrator password" : "Password";
  return new Response(`<!doctype html><html lang="en-GB"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Engagement letters</title>
<style>
 body{margin:0;min-height:100vh;display:grid;place-items:center;background:#EEF3FB;color:#0C1A2E;
  font:13px/1.55 system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
 form{background:#fff;border:1px solid #DDE8F5;border-radius:12px;padding:26px 28px;width:320px}
 h1{font-size:16px;margin:0 0 2px}
 p{margin:0 0 18px;font-size:11.5px;color:#7A96B8}
 label{display:block;font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
  color:#7A96B8;margin-bottom:5px}
 input{width:100%;box-sizing:border-box;height:34px;padding:6px 9px;font:13px/1.4 inherit;
  border:1px solid #DDE8F5;border-radius:8px;background:#fff;color:#0C1A2E}
 input:focus{border-color:#1550AA;outline:none}
 button{margin-top:14px;width:100%;height:34px;border:0;border-radius:8px;background:#1550AA;
  color:#fff;font:700 13px/1 inherit;cursor:pointer}
 button:hover{background:#0E3D88}
 .err{margin-top:12px;font-size:11.5px;color:#DC2626}
</style></head><body>
<form method="POST">
 <h1>Engagement letters</h1>
 <p>Luckmans Duckett Parker${scope === "admin" ? " &middot; administration" : ""}</p>
 <label for="p">${label}</label>
 <input id="p" name="password" type="password" autocomplete="current-password" autofocus>
 <button type="submit">Continue</button>
 ${message ? `<div class="err">${message}</div>` : ""}
</form></body></html>`,
    { status: 401, headers: { "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow" } });
}

export async function onRequest(context) {
  const { request, env, next } = context;
  const url = new URL(request.url);
  const admin = url.pathname === "/admin" || url.pathname.startsWith("/admin/");
  const scope = admin ? "admin" : "site";
  const expected = admin ? env.ADMIN_PASSWORD : env.SITE_PASSWORD;
  const secret = env.SESSION_SECRET;

  if (!expected || !secret) {
    return new Response(
      "This deployment is not configured. Set SITE_PASSWORD, ADMIN_PASSWORD and "
      + "SESSION_SECRET in the Pages project settings.",
      { status: 503, headers: { "Content-Type": "text/plain" } });
  }

  if (await cookieValid(readCookie(request, "loe_" + scope), scope, secret)) return next();

  if (request.method === "POST") {
    const form = await request.formData();
    if (same(String(form.get("password") || ""), expected)) {
      const cookie = await makeCookie(scope, secret);
      return new Response(null, { status: 303, headers: {
        Location: url.pathname,
        "Set-Cookie": `loe_${scope}=${cookie}; Path=${admin ? "/admin" : "/"}; `
          + `Max-Age=${MAX_AGE}; HttpOnly; Secure; SameSite=Lax`,
      }});
    }
    return loginPage(scope, "That password was not accepted.");
  }

  return loginPage(scope, "");
}
