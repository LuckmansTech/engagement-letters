/* IndexedDB-backed shim for the window.storage API that the Claude artifact
   runtime provides. Same three method names and the same return shapes, so the
   component's call sites are untouched. IndexedDB rather than localStorage
   because a base64'd .docx letterhead will exceed the ~5MB localStorage quota. */
const DB = "loe", STORE = "kv";

function open() {
  return new Promise((res, rej) => {
    const rq = indexedDB.open(DB, 1);
    rq.onupgradeneeded = () => rq.result.createObjectStore(STORE);
    rq.onsuccess = () => res(rq.result);
    rq.onerror = () => rej(rq.error);
  });
}
function tx(mode, fn) {
  return open().then((db) => new Promise((res, rej) => {
    const t = db.transaction(STORE, mode), rq = fn(t.objectStore(STORE));
    rq.onsuccess = () => res(rq.result);
    rq.onerror = () => rej(rq.error);
    t.oncomplete = () => db.close();
  }));
}
if (!window.storage) {
  window.storage = {
    async get(key) {
      const v = await tx("readonly", (s) => s.get(key));
      return v === undefined ? null : { key, value: v };
    },
    async set(key, value) { await tx("readwrite", (s) => s.put(value, key)); return { key, value }; },
    async delete(key) { await tx("readwrite", (s) => s.delete(key)); return { key, deleted: true }; },
    async list(prefix = "") {
      const keys = await tx("readonly", (s) => s.getAllKeys());
      return { keys: keys.filter((k) => String(k).startsWith(prefix)), prefix };
    },
  };
}
