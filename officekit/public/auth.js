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
  if (location.pathname === '/auth/finish') history.replaceState(null, '', '/auth/finish');
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
  if (form) {
    if (form.dataset.mode === 'complete' && !validLink) {
      showError('This sign-in link is missing or invalid. Request a new link from the sign-in page.');
      form.querySelector('button').disabled = true;
      const link = document.createElement('a'); link.href='/signup'; link.textContent='Request a new sign-in link →'; link.className='text-link'; form.after(link);
    }
    // Explicit confirmation on every device; GET and email scanners do not sign in.
    form.addEventListener('submit', async event => {
      event.preventDefault();
      if (!form.reportValidity()) return;
      const button=form.querySelector('button'), original=button.textContent;
      button.disabled=true;button.textContent='Please wait…';errorBox.hidden=true;statusBox.hidden=true;
      try {
        const email=emailInput.value.trim();
        if (form.dataset.mode === 'complete') {
          const result = await request('/api/auth/complete', {email, code});
          location.replace(result.next === '/cli' ? '/cli' : '/app');
        } else {
          await request('/api/auth/email', {email});
          statusBox.textContent='Check your inbox for your sign-in link. Keep this page open, or finish on another device. If it doesn’t arrive, check your spam folder.';
          statusBox.hidden=false;
          button.textContent='Send another link';
        }
      } catch (error) { showError(error.message === 'Failed to fetch' ? 'The service could not be reached. Check your connection and try again.' : error.message); }
      finally {button.disabled=false;if(button.textContent==='Please wait…')button.textContent=original;}
    });
  }
  const deviceForm = document.getElementById('device-form');
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
