# Multiplayer Chat & User List Pattern

Add real-time chat and user presence to any canvas page using the signaling server.

## Server Info

- **URL**: `https://dev-test-dev.jam-bot.com`
- **Source reference**: `~/Websites/3D-threejs-site/index.html` — grep for handler patterns
- **Socket events**: user-spawn, chat-message, user-name-change, world-state, user-joined, user-left, user-count-update

## Socket.io Script Tag

Must go BEFORE the importmap in `<head>`:

```html
<script src="https://cdn.jsdelivr.net/npm/socket.io-client@4.7.2/dist/socket.io.min.js"></script>
```

## HTML Structure

### Welcome Dialog (overlay)

```html
<div id="welcome-overlay" style="position:fixed;inset:0;background:rgba(0,0,0,0.85);z-index:9999;display:flex;align-items:center;justify-content:center;">
  <div style="background:rgba(20,25,35,0.95);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.15);border-radius:20px;padding:40px;text-align:center;max-width:360px;width:90%;">
    <h2 style="color:#e2e8f0;font-size:22px;margin-bottom:8px;">Welcome</h2>
    <p style="color:#8b949e;font-size:14px;margin-bottom:20px;">Enter your name to join</p>
    <input type="text" id="welcome-input" maxlength="20" placeholder="Your name..." style="width:100%;padding:12px 16px;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.2);border-radius:10px;color:#e2e8f0;font-size:16px;outline:none;margin-bottom:16px;">
    <button id="welcome-button" style="width:100%;padding:12px;background:rgba(59,130,246,0.8);border:none;border-radius:10px;color:#fff;font-size:16px;font-weight:600;cursor:pointer;">Join Room</button>
  </div>
</div>
```

### User List (top-left, collapsible)

```html
<button id="user-list-toggle" style="position:fixed;top:16px;left:16px;z-index:210;background:rgba(0,0,0,0.7);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.2);color:#e2e8f0;padding:6px 12px;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer;">👥 Users</button>
<div id="user-list" style="position:fixed;top:60px;left:16px;z-index:210;background:rgba(0,0,0,0.7);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.15);border-radius:12px;padding:12px 16px;min-width:160px;transition:all 0.3s;transform-origin:top left;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
    <h3 style="margin:0;color:#e2e8f0;font-size:13px;">Users Online <span id="user-count-badge" style="color:#8b949e;">(1)</span></h3>
    <button id="user-list-close" style="background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);color:#e2e8f0;font-size:16px;width:22px;height:22px;border-radius:50%;cursor:pointer;display:flex;align-items:center;justify-content:center;padding:0;">×</button>
  </div>
  <div id="user-list-content">
    <div id="current-user" style="margin:4px 0;color:#e2e8f0;font-size:12px;padding:4px 8px;border-radius:6px;background:rgba(74,144,226,0.2);font-weight:600;">Loading...</div>
  </div>
</div>
```

### Chat Box (bottom-right, hidden by default)

```html
<div id="chat-container" style="position:fixed;bottom:16px;right:16px;width:280px;z-index:210;display:none;flex-direction:column;">
  <div id="chat-messages" style="max-height:150px;overflow-y:auto;padding:10px 12px;font-size:13px;background:rgba(0,0,0,0.7);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.15);border-radius:12px 12px 0 0;scrollbar-width:none;"></div>
  <div style="display:flex;gap:6px;background:rgba(0,0,0,0.7);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.15);border-top:none;border-radius:0 0 12px 12px;padding:8px;">
    <input type="text" id="chat-input" maxlength="200" placeholder="Type message..." style="flex:1;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);color:#e2e8f0;padding:8px 10px;border-radius:8px;font-size:13px;outline:none;min-width:0;">
    <button id="chat-send" style="background:rgba(59,130,246,0.8);border:none;color:#fff;padding:8px 12px;border-radius:8px;cursor:pointer;font-size:12px;font-weight:600;flex-shrink:0;">Send</button>
  </div>
</div>
<button id="chat-toggle" style="position:fixed;bottom:16px;right:16px;z-index:210;width:32px;height:32px;background:rgba(0,0,0,0.7);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.2);border-radius:50%;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:16px;color:#e2e8f0;">💬</button>
```

## JavaScript

### Core Setup

```javascript
(function() {
  const SIGNALING_SERVER = 'https://dev-test-dev.jam-bot.com';
  let socket = null;
  let myUserId = null;
  let userChosenName = localStorage.getItem('office-username') || '';
  const userAvatars = new Map(); // userId -> { username }

  // Welcome dialog
  const welcomeInput = document.getElementById('welcome-input');
  if (userChosenName) welcomeInput.value = userChosenName;
  document.getElementById('welcome-button').addEventListener('click', joinRoom);
  welcomeInput.addEventListener('keydown', e => { if (e.key === 'Enter') joinRoom(); });

  function joinRoom() {
    const name = welcomeInput.value.trim() || 'Anonymous';
    userChosenName = name;
    localStorage.setItem('office-username', name);
    document.getElementById('welcome-overlay').style.display = 'none';
    initSocket(name);
  }

  function initSocket(username) {
    socket = io(SIGNALING_SERVER, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    });

    socket.on('connect', () => {
      myUserId = socket.id;
      userAvatars.clear();
      userAvatars.set(myUserId, { username });
      socket.emit('user-spawn', {
        position: { x: 0, y: 0, z: 5 },
        rotation: { x: 0, y: 0, z: 0 },
        username
      });
      updateUserList();
    });

    socket.on('world-state', (data) => {
      if (data.users) data.users.forEach(([uid, avatar]) => {
        if (uid !== socket.id) userAvatars.set(uid, { username: avatar.username || 'User' });
      });
      if (data.chatHistory) data.chatHistory.forEach(msg => displayChatMessage(msg));
      updateUserList();
    });

    socket.on('user-joined', (avatar) => {
      if (avatar.id !== socket.id) {
        userAvatars.set(avatar.id, { username: avatar.username || 'User' });
        displaySystemMessage(avatar.username + ' joined the room');
      }
      updateUserList();
    });

    socket.on('user-left', (data) => {
      const user = userAvatars.get(data.userId);
      if (user) displaySystemMessage(user.username + ' left the room');
      userAvatars.delete(data.userId);
      updateUserList();
    });

    socket.on('chat-message', displayChatMessage);

    socket.on('user-name-changed', (data) => {
      if (userAvatars.has(data.userId)) userAvatars.get(data.userId).username = data.newName;
      displaySystemMessage(data.oldName + ' is now ' + data.newName);
      updateUserList();
    });

    socket.on('disconnect', () => displaySystemMessage('Disconnected from server'));
  }
```

### Chat Functions

```javascript
  function escapeHtml(str) { const d = document.createElement('div'); d.textContent = str; return d.innerHTML; }

  function displayChatMessage(msg) {
    const container = document.getElementById('chat-messages');
    if (!container) return;
    const el = document.createElement('div');
    el.style.margin = '2px 0';
    el.style.wordWrap = 'break-word';
    if (msg.isSystem) {
      el.innerHTML = '<span style="color:#f59e0b;font-style:italic;font-size:12px;">🔔 ' + escapeHtml(msg.message) + '</span>';
    } else {
      el.innerHTML = '<span style="color:#4aff4a;font-weight:700;">' + escapeHtml(msg.username) + ':</span> <span style="color:#e2e8f0;">' + escapeHtml(msg.message) + '</span>';
    }
    container.appendChild(el);
    container.scrollTop = container.scrollHeight;
    while (container.children.length > 50) container.removeChild(container.firstChild);
  }

  function displaySystemMessage(text) {
    displayChatMessage({ username: 'System', message: text, isSystem: true });
  }

  function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg || !socket || !socket.connected) return;
    socket.emit('chat-message', { message: msg });
    input.value = '';
  }

  // Chat toggle
  let chatVisible = false;
  document.getElementById('chat-toggle').addEventListener('click', () => {
    chatVisible = !chatVisible;
    document.getElementById('chat-container').style.display = chatVisible ? 'flex' : 'none';
    document.getElementById('chat-toggle').style.display = chatVisible ? 'none' : 'flex';
  });
  document.getElementById('chat-send').addEventListener('click', sendChatMessage);
  document.getElementById('chat-input').addEventListener('keydown', e => { if (e.key === 'Enter') sendChatMessage(); });
```

### User List Functions

```javascript
  function updateUserList() {
    const content = document.getElementById('user-list-content');
    const currentUserEl = document.getElementById('current-user');
    const badge = document.getElementById('user-count-badge');
    if (!content) return;
    if (badge) badge.textContent = '(' + userAvatars.size + ')';

    if (currentUserEl && myUserId) {
      const me = userAvatars.get(myUserId);
      const nameSpan = document.createElement('span');
      nameSpan.textContent = me ? me.username : 'You';
      nameSpan.style.cursor = 'pointer';
      nameSpan.style.textDecoration = 'underline';
      nameSpan.style.color = '#4aff4a';
      nameSpan.addEventListener('click', editUserName);
      const youLabel = document.createElement('span');
      youLabel.textContent = ' (You)';
      youLabel.style.color = '#8b949e';
      currentUserEl.innerHTML = '';
      currentUserEl.appendChild(nameSpan);
      currentUserEl.appendChild(youLabel);
    }

    content.querySelectorAll('.user-item:not(.self)').forEach(el => el.remove());
    userAvatars.forEach((avatar, uid) => {
      if (uid !== myUserId) {
        const item = document.createElement('div');
        item.className = 'user-item';
        item.style.cssText = 'margin:4px 0;color:#e2e8f0;font-size:12px;padding:4px 8px;border-radius:6px;background:rgba(255,255,255,0.05);';
        item.textContent = avatar.username;
        content.appendChild(item);
      }
    });
  }

  function editUserName() {
    const el = document.getElementById('current-user');
    if (!el || !myUserId) return;
    const me = userAvatars.get(myUserId);
    const nameSpan = el.querySelector('span');
    if (!nameSpan) return;
    const input = document.createElement('input');
    input.type = 'text';
    input.value = me ? me.username : '';
    input.maxLength = 20;
    input.style.cssText = 'background:rgba(0,0,0,0.8);border:1px solid #4aff4a;color:white;padding:2px 5px;border-radius:3px;font-size:12px;width:90px;';
    nameSpan.style.display = 'none';
    el.insertBefore(input, nameSpan);
    input.focus(); input.select();
    const save = () => {
      const newName = input.value.trim();
      if (newName && me && newName !== me.username) {
        me.username = newName;
        localStorage.setItem('office-username', newName);
        if (socket && socket.connected) socket.emit('user-name-change', { userId: myUserId, newName });
      }
      input.remove(); nameSpan.style.display = 'inline'; updateUserList();
    };
    input.addEventListener('blur', save);
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter') { e.preventDefault(); save(); }
      if (e.key === 'Escape') { e.preventDefault(); input.remove(); nameSpan.style.display = 'inline'; }
    });
  }

  // User list toggle
  let userListOpen = false;
  document.getElementById('user-list-toggle').addEventListener('click', () => {
    userListOpen = true;
    document.getElementById('user-list').style.opacity = '1';
    document.getElementById('user-list').style.transform = 'scale(1)';
    document.getElementById('user-list').style.pointerEvents = 'auto';
    document.getElementById('user-list-toggle').style.display = 'none';
  });
  document.getElementById('user-list-close').addEventListener('click', () => {
    userListOpen = false;
    document.getElementById('user-list').style.opacity = '0';
    document.getElementById('user-list').style.transform = 'scale(0)';
    document.getElementById('user-list').style.pointerEvents = 'none';
    document.getElementById('user-list-toggle').style.display = 'block';
  });
})();
```
