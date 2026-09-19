'use strict';
(() => {
  const picker = document.getElementById('office-folder');
  if (!picker) return;
  const review = document.getElementById('import-review');
  const errorBox = document.getElementById('auth-error');
  const statusBox = document.getElementById('import-status');
  const upload = document.getElementById('upload-office');
  const cancel = document.getElementById('cancel-import');
  const progress = document.getElementById('import-progress');
  const replacement = document.getElementById('import-replace');
  const confirm = document.getElementById('replace-confirm');
  const encoder = new TextEncoder();
  let prepared = null, controller = null, busy = false;

  function csrf() {
    const value = document.cookie.split('; ').find(c => c.startsWith('__Host-wp_csrf='));
    return value ? decodeURIComponent(value.split('=')[1]) : '';
  }
  async function request(path, data, signal) {
    const response = await fetch(path, {method:data === undefined ? 'GET' : 'POST', credentials:'same-origin', signal,
      headers:data === undefined ? {} : {'Content-Type':'application/json', 'X-CSRF-Token':csrf()},
      body:data === undefined ? undefined : JSON.stringify(data)});
    let result;
    try { result = await response.json(); } catch (_) { throw new Error('The server could not complete this request. Please retry.'); }
    if (!response.ok) {
      const error = new Error(response.status === 401 ? 'Your sign-in expired. Sign in again, then select the folder to resume.' : result.error || 'The upload could not be completed.');
      error.status = response.status;
      throw error;
    }
    return result;
  }
  function fail(error) {
    errorBox.textContent = error.message || 'The office could not be prepared. Choose the folder and try again.';
    if (error.status === 401) {
      const a = document.createElement('a'); a.href='/signup'; a.textContent=' Sign in again →'; errorBox.append(a);
    }
    errorBox.hidden = false;
  }
  function status(text) { statusBox.textContent=text; statusBox.hidden=false; }
  function canonical(value) {
    if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
    if (value && typeof value === 'object') return '{' + Object.keys(value).sort().map(k => JSON.stringify(k)+':'+canonical(value[k])).join(',') + '}';
    return JSON.stringify(value);
  }
  async function hash(bytes) {
    return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), n => n.toString(16).padStart(2, '0')).join('');
  }
  function allowed(name, rules) {
    const parts = name.split('/');
    if (!name || name.includes('\\') || parts.some(p => !p || p.startsWith('.'))) return false;
    if (parts.length === 1) return rules.root_files.includes(name);
    const suffix = name.slice(name.lastIndexOf('.')).toLowerCase();
    return rules.retained.includes(parts[0]) && rules.suffixes.includes(suffix) && !/(credential|secret|token|api.?key)/i.test(name);
  }
  function encode(bytes) {
    let binary = '';
    for (let i=0;i<bytes.length;i+=8192) binary += String.fromCharCode(...bytes.subarray(i,i+8192));
    return btoa(binary);
  }
  function ready() { upload.disabled = busy || !prepared || (!replacement.hidden && !confirm.checked); }
  confirm.addEventListener('change', ready);
  if (!('webkitdirectory' in picker) || !crypto.subtle) {
    document.getElementById('folder-unsupported').hidden=false; picker.disabled=true; return;
  }
  picker.addEventListener('change', async () => {
    prepared=null; review.hidden=true; errorBox.hidden=true; confirm.checked=false; ready();
    const selected=Array.from(picker.files || []);
    if (!selected.length) return;
    picker.disabled=true;
    status('Preparing your review on this computer. No files have been uploaded.');
    try {
      const [rules, listing] = await Promise.all([request('/api/browser-migrations/config'), request('/api/offices')]);
      const root=selected[0].webkitRelativePath.split('/')[0];
      const files=[], names=new Set(); let bytes=0;
      for (const file of selected) {
        if (!file.webkitRelativePath.startsWith(root+'/')) throw new Error('Select one saved office folder.');
        const name=file.webkitRelativePath.slice(root.length+1);
        if (!allowed(name,rules)) continue;
        if (names.has(name)) throw new Error('The selected folder contains duplicate document names.');
        names.add(name); bytes+=file.size; files.push({name,file});
      }
      if (!names.has('answers.json') || !names.has('balance_sheet.json')) throw new Error('Choose the saved office folder containing answers.json and balance_sheet.json, rather than the repository or a parent folder.');
      if (files.length>rules.max_files || bytes>rules.max_bytes) throw new Error('This office exceeds the 64 MiB / 1,024 document limit. Use a smaller saved office copy.');
      files.sort((a,b) => a.name < b.name ? -1 : a.name > b.name ? 1 : 0);
      const documents=[], chunks=new Map(); let answers, balance;
      for (const {name,file} of files) {
        const data=new Uint8Array(await file.arrayBuffer());
        if (data.byteLength!==file.size) throw new Error('A selected file changed. Choose the folder again.');
        if (name==='answers.json' || name==='balance_sheet.json') {
          let parsed;
          try { parsed=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(data)); }
          catch (_) { throw new Error('The saved answers or balance sheet is not valid JSON. Rebuild the office locally first.'); }
          if (name==='answers.json') answers=parsed; else balance=parsed;
        }
        const parts=[];
        for (let offset=0;offset<data.length;offset+=rules.chunk_bytes) {
          const part=data.slice(offset,offset+rules.chunk_bytes), digest=await hash(part);
          chunks.set(digest,part); parts.push(digest);
        }
        documents.push({path:name,size:data.length,sha256:await hash(data),chunks:parts});
      }
      if (!answers || !balance || typeof answers.office_id!=='string' || !/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/i.test(answers.office_id) || answers.office_id!==balance.office_id || answers.as_of!==balance.as_of) {
        throw new Error('The saved answers and balances must belong to the same built office and date. Rebuild locally first.');
      }
      const manifest={v:rules.version,office_id:answers.office_id,files:documents};
      const digest=await hash(encoder.encode(canonical(manifest)));
      const current=listing.offices.find(o=>o.office_id===answers.office_id);
      prepared={manifest,digest,chunks,current};
      const name=typeof answers.owner==='string' ? answers.owner : 'Your office';
      const excluded=selected.length-files.length;
      document.getElementById('import-summary').textContent=name+' · balances as of '+String(balance.as_of)+' · '+files.length+' documents · '+(bytes/1048576).toFixed(2)+' MiB. '+excluded+' other '+(excluded===1?'file':'files')+' excluded.';
      const list=document.getElementById('import-files'); list.replaceChildren();
      for (const f of documents) { const li=document.createElement('li'); li.textContent=f.path+' · '+f.size.toLocaleString()+' bytes'; list.append(li); }
      replacement.hidden=!current || current.digest===digest;
      document.getElementById('replace-summary').textContent=current ? 'This office is already online, with balances as of '+current.as_of+'. Review the selected files before replacing its saved records.' : '';
      document.getElementById('replace-current').href='/app/offices/'+answers.office_id;
      review.hidden=false;
      status('Ready to review. Your files are still only on this computer.');
      review.scrollIntoView({block:'start',behavior:'smooth'});
    } catch (error) { prepared=null; statusBox.hidden=true; fail(error); }
    finally { picker.disabled=false; ready(); }
  });
  cancel.addEventListener('click',()=>controller?.abort());
  upload.addEventListener('click',async()=>{
    if (busy || !prepared || (!replacement.hidden && !confirm.checked)) return;
    const selected=prepared; busy=true; controller=new AbortController();
    picker.disabled=true; confirm.disabled=true; cancel.hidden=false; cancel.disabled=false;
    progress.hidden=false; progress.value=0; errorBox.hidden=true; ready();
    try {
      status('Starting a private upload…');
      const state=await request('/api/browser-migrations',{manifest:selected.manifest},controller.signal);
      if (state.digest!==selected.digest || !Array.isArray(state.missing) || state.missing.some(h=>!selected.chunks.has(h))) throw new Error('The upload does not match the reviewed files. Select the folder again.');
      let done=0;
      for (const digest of state.missing) {
        status('Uploading '+(done+1)+' of '+state.missing.length+' file parts…');
        await request('/api/browser-migrations/'+state.digest+'/chunks',{sha256:digest,data:encode(selected.chunks.get(digest))},controller.signal);
        progress.value=++done/state.missing.length*100;
      }
      // Activation is a commit: do not offer cancellation with an uncertain result.
      controller.signal.throwIfAborted(); cancel.disabled=true;
      status('Verifying saved records and opening your office…'); progress.value=100;
      const receipt=await request('/api/browser-migrations/'+state.digest+'/activate',{
        replace_revision:!replacement.hidden ? selected.current.digest : null});
      const destination='/app/offices/'+selected.manifest.office_id;
      if (receipt.status!=='active' || receipt.digest!==state.digest || receipt.path!==destination) throw new Error('The completion receipt could not be verified. Check your workspace before retrying.');
      status('Your hosted office is ready. Opening it now…'); location.assign(destination);
    } catch(error) {
      if (error.name==='AbortError') status('Upload stopped. Your hosted office was not replaced. Choose Upload and open office to resume.');
      else { statusBox.hidden=true; fail(error); }
    } finally {
      busy=false; controller=null; picker.disabled=false; confirm.disabled=false; cancel.hidden=true; ready();
    }
  });
})();
