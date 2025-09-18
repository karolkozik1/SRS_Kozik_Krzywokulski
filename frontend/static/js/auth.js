(function () {
  const TOKEN_KEY = 'access_token';
  const TYPE_KEY  = 'token_type';
  const DEFAULT_TYPE = 'Bearer';

  function token()     { return localStorage.getItem(TOKEN_KEY) || ''; }
  function tokenType() { return localStorage.getItem(TYPE_KEY)  || DEFAULT_TYPE; }
  function isLoggedIn(){ return !!token(); }

  function setAuthUI() {
    const logged = isLoggedIn();
    document.querySelectorAll('[data-auth="guest"]').forEach(el => el.style.display = logged ? 'none' : '');
    document.querySelectorAll('[data-auth="user"]').forEach(el  => el.style.display = logged ? '' : 'none');
  }

  function authHeader() {
    const t = token();
    return t ? { Authorization: `${tokenType()} ${t}` } : {};
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(TYPE_KEY);
    setAuthUI();
    // dokąd po wylogowaniu – domyślnie /login
    const after = document.body.getAttribute('data-redirect-logout') || '/';
    window.location.href = after;
  }

  // wystawiamy globalnie
  window.auth = { token, tokenType, isLoggedIn, setAuthUI, authHeader, logout };

  // inicjalizacja po załadowaniu dokumentu
  document.addEventListener('DOMContentLoaded', () => {
    setAuthUI();

    // przycisk Wyloguj
    const btn = document.getElementById('nav-logout');
    if (btn) btn.addEventListener('click', (e) => { e.preventDefault(); logout(); });

    // miękka ochrona linków wymagających logowania
    document.querySelectorAll('[data-require-auth]').forEach(a => {
      a.addEventListener('click', (ev) => {
        if (!isLoggedIn()) {
          ev.preventDefault();
          const target = a.getAttribute('href') || '/';
          window.location.href = `/login?next=${encodeURIComponent(target)}`;
        }
      });

    });

  });

  
  window.auth = {
  getToken,
  isLoggedIn,
  logout,
  setAuthUI
};
})();

  window.auth.getToken = function() {
  return localStorage.getItem("access_token");
};

