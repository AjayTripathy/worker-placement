'use strict';
(() => {
  let errorBox = document.getElementById('auth-error');
  if (!errorBox) { errorBox=document.createElement('div'); errorBox.className='notice error'; errorBox.setAttribute('role','alert'); errorBox.hidden=true; document.querySelector('main').prepend(errorBox); }
  const statusBox = document.getElementById('auth-status');
  const form = document.getElementById('auth-form');
  const emailInput = document.getElementById('email');
  const params = new URLSearchParams(location.search);
  // Keep the one-time code only in this page's memory, never localStorage.
  const code = params.get('oobCode');
  const validLink = params.get('mode') === 'signIn' && !!code;
  const googleQuery = location.pathname === '/auth/google/finish' ? location.search.slice(1) : '';
  if (location.pathname === '/auth/finish' || location.pathname === '/auth/google/finish') history.replaceState(null, '', location.pathname);
  function showError(text) { errorBox.textContent = text; errorBox.hidden = false; }
  function csrf() {
    const cookie = document.cookie.split('; ').find(v => v.startsWith('__Host-wp_csrf='));
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : '';
  }
  async function request(path, body) {
    const response = await fetch(path, {method:'POST', credentials:'same-origin', headers:{'Content-Type':'application/json', 'X-CSRF-Token':csrf()}, body:JSON.stringify(body)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'The request could not be completed. Please try again.');
    return data;
  }
  const google = document.getElementById('google-signin');
  function openWorkspace(result) { location.replace(result.next === '/cli' ? '/cli' : '/app'); }
  if (google) {
    google.addEventListener('click', async () => {
      google.disabled=true; errorBox.hidden=true; statusBox.hidden=true;
      google.textContent='Opening Google…';
      try {
        const result = await request('/api/auth/google/start', {});
        const target = new URL(result.url);
        if (target.origin !== 'https://accounts.google.com') throw new Error('Google sign-in is unavailable. Please try again.');
        location.assign(target.href);
      } catch (error) { showError(error.message); google.disabled=false; google.textContent='Continue with Google'; }
    });
    if (google.dataset.finish === 'true') {
      google.disabled=true; statusBox.textContent='Finishing your sign-in…';statusBox.hidden=false;
      request('/api/auth/google/complete', {query:googleQuery})
        .then(openWorkspace)
        .catch(error => { showError(error.message); google.disabled=false; statusBox.hidden=true; });
    }
  }
  if (form) {
    if (!validLink) {
      showError('This old sign-in link is missing or invalid. Continue with Google from the sign-in page.');
      form.querySelector('button').disabled = true;
    }
    form.addEventListener('submit', async event => {
      event.preventDefault();
      if (!form.reportValidity()) return;
      const button=form.querySelector('button'), original=button.textContent;
      button.disabled=true;button.textContent='Please wait…';errorBox.hidden=true;
      try { openWorkspace(await request('/api/auth/complete', {email:emailInput.value.trim(), code})); }
      catch (error) { showError(error.message); button.disabled=false;button.textContent=original; }
    });
  }
  const deviceForm = document.getElementById('device-form');
  const startOffice = document.getElementById('start-office');
  if (startOffice) startOffice.addEventListener('click', async () => {
    startOffice.disabled=true; errorBox.hidden=true;
    try {
      const office=await request('/api/offices/start', {});
      if (!/^\/app\/offices\/[a-f0-9-]{36}$/.test(office.path)) throw new Error('Could not open your office. Please try again.');
      location.assign(office.path);
    } catch(error) {showError(error.message); startOffice.disabled=false;}
  });
  if(deviceForm) deviceForm.addEventListener('submit', async event => {
    event.preventDefault(); const button=deviceForm.querySelector('button');button.disabled=true;errorBox.hidden=true;
    try {
      await request('/api/cli/approve', {device:deviceForm.elements.device.value, code:deviceForm.elements.code.value});
      statusBox.textContent='Device connected. Return to your local app or terminal.';statusBox.hidden=false;deviceForm.hidden=true;
    } catch(error) {showError(error.message);button.disabled=false;}
  });
  const signout=document.getElementById('sign-out');
  if(signout)signout.addEventListener('click',async()=>{
    signout.disabled=true;
    try{await request('/api/auth/logout',{});location.replace('/');}
    catch(_){showError('Could not sign out. Check your connection and try again.');signout.disabled=false;}
  });
})();
