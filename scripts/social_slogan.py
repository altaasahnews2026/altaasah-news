from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')
style='''<style id="social-slogan-style">
.brand small{display:block!important;color:#df1727!important;font-size:17px!important;line-height:1.35!important;font-weight:900!important;margin-top:-2px!important}
.footer .slogan{color:#fff;font-size:24px;font-weight:900;line-height:1.4;margin:4px 0 10px}
.footer .social{display:flex;align-items:center;gap:9px;flex-wrap:wrap;direction:ltr;margin-top:12px}
.footer .social a{display:inline-flex!important;align-items:center;justify-content:center;width:40px;height:40px;border-radius:50%;background:#fff;color:#071b33!important;border:1px solid rgba(255,255,255,.2);font-size:19px!important;font-weight:900;transition:transform .15s,opacity .15s}
.footer .social a:hover{transform:translateY(-2px);opacity:.9}.footer .social svg{width:20px;height:20px;fill:currentColor}
@media(max-width:700px){.brand small{font-size:15px!important}.footer .slogan{font-size:20px}.footer .social a{width:38px;height:38px}}
</style>'''
s=re.sub(r'<style id="social-slogan-style">.*?</style>','',s,flags=re.S)
s=s.replace('</head>',style+'</head>',1)
icons='''<div class="social" aria-label="منصات التواصل الاجتماعي">
<a href="https://www.facebook.com/" target="_blank" rel="noopener" aria-label="Facebook" title="Facebook"><svg viewBox="0 0 24 24"><path d="M13.6 21v-8h2.7l.4-3h-3.1V8.1c0-.9.3-1.5 1.6-1.5h1.7V4c-.3 0-1.2-.1-2.2-.1-2.2 0-3.7 1.3-3.7 3.8V10H8.5v3h2.5v8h2.6Z"/></svg></a>
<a href="https://x.com/" target="_blank" rel="noopener" aria-label="X" title="X"><svg viewBox="0 0 24 24"><path d="M18.9 3H22l-6.8 7.8L23.2 21h-6.3l-5-6.1L6.6 21H3.5l7.3-8.4L3 3h6.4l4.5 5.7L18.9 3Zm-1.1 15.9h1.7L8.5 5H6.7l11.1 13.9Z"/></svg></a>
<a href="https://www.instagram.com/" target="_blank" rel="noopener" aria-label="Instagram" title="Instagram"><svg viewBox="0 0 24 24"><path d="M7 2h10a5 5 0 0 1 5 5v10a5 5 0 0 1-5 5H7a5 5 0 0 1-5-5V7a5 5 0 0 1 5-5Zm0 2a3 3 0 0 0-3 3v10a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3V7a3 3 0 0 0-3-3H7Zm5 3.5A4.5 4.5 0 1 1 12 16.5 4.5 4.5 0 0 1 12 7.5Zm0 2A2.5 2.5 0 1 0 12 14.5 2.5 2.5 0 0 0 12 9.5ZM17.5 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2Z"/></svg></a>
<a href="https://www.tiktok.com/" target="_blank" rel="noopener" aria-label="TikTok" title="TikTok"><svg viewBox="0 0 24 24"><path d="M15 2h3c.3 2 1.5 3.5 3.5 4v3.1a8.5 8.5 0 0 1-3.5-1V15a6 6 0 1 1-6-6c.4 0 .7 0 1 .1v3.2a3 3 0 1 0 1 2.7V2Z"/></svg></a>
<a href="https://www.youtube.com/" target="_blank" rel="noopener" aria-label="YouTube" title="YouTube"><svg viewBox="0 0 24 24"><path d="M23 7.2a3 3 0 0 0-2.1-2.1C19 4.5 12 4.5 12 4.5s-7 0-8.9.6A3 3 0 0 0 1 7.2 31 31 0 0 0 .5 12 31 31 0 0 0 1 16.8a3 3 0 0 0 2.1 2.1c1.9.6 8.9.6 8.9.6s7 0 8.9-.6a3 3 0 0 0 2.1-2.1 31 31 0 0 0 .5-4.8 31 31 0 0 0-.5-4.8ZM10 15.5v-7l6 3.5-6 3.5Z"/></svg></a>
<a href="https://t.me/" target="_blank" rel="noopener" aria-label="Telegram" title="Telegram"><svg viewBox="0 0 24 24"><path d="m21.5 3.5-3 17c-.2 1.2-.9 1.5-1.9.9l-5.2-3.8-2.5 2.4c-.3.3-.5.5-1 .5l.4-5.3 9.7-8.8c.4-.4-.1-.6-.6-.2L5.4 13.9.3 12.3c-1.1-.3-1.1-1.1.2-1.5l19.9-7.7c.9-.3 1.7.2 1.1 1.4Z"/></svg></a>
<a href="https://wa.me/" target="_blank" rel="noopener" aria-label="WhatsApp" title="WhatsApp"><svg viewBox="0 0 24 24"><path d="M20.5 3.5A11.8 11.8 0 0 0 12 0 12 12 0 0 0 1.6 18.1L0 24l6-1.6A12 12 0 0 0 24 12a11.8 11.8 0 0 0-3.5-8.5ZM12 21.8a9.8 9.8 0 0 1-5-1.4l-.4-.2-3.6 1 1-3.5-.2-.4A9.8 9.8 0 1 1 12 21.8Zm5.4-7.3c-.3-.2-1.8-.9-2.1-1-.3-.1-.5-.2-.7.2l-.8 1c-.2.2-.3.3-.6.1a8 8 0 0 1-2.3-1.4 8.8 8.8 0 0 1-1.6-2c-.2-.3 0-.5.2-.7l.5-.6c.2-.2.2-.4.3-.6.1-.2 0-.4 0-.5-.1-.2-.7-1.7-.9-2.3-.2-.6-.5-.5-.7-.5h-.6c-.2 0-.5.1-.7.3-.2.3-1 1-1 2.4s1 2.8 1.2 3c.2.2 2 3.1 4.9 4.3.7.3 1.3.5 1.7.6.7.2 1.4.2 1.9.1.6-.1 1.8-.7 2.1-1.4.3-.7.3-1.3.2-1.4-.1-.1-.3-.2-.6-.3Z"/></svg></a>
</div>'''
s=re.sub(r'<div class="social">.*?</div>',icons,s,count=1,flags=re.S)
if 'class="slogan"' not in s:
    s=s.replace('<img class="footlogo" src="./assets/logo.svg" alt="التاسعة نيوز">','<img class="footlogo" src="./assets/logo.svg" alt="التاسعة نيوز"><div class="slogan">نعلم لتعلم</div>',1)
p.write_text(s,encoding='utf-8')
print('SOCIAL ICONS + CLEAR SLOGAN APPLIED')
