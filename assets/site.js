(()=>{'use strict';
const $=s=>document.querySelector(s),$$=s=>Array.from(document.querySelectorAll(s));
document.addEventListener('DOMContentLoaded',()=>{
 const now=new Date(),fmt={weekday:'long',day:'numeric',month:'long',year:'numeric'};
 const date=$('#today'),heroDate=$('#heroDate'),year=$('#year');
 let stamp='';try{stamp=new Intl.DateTimeFormat('ar-IQ',fmt).format(now)}catch(e){stamp='التاسعة نيوز'}
 if(date)date.textContent=stamp+' — العراق';if(heroDate)heroDate.textContent=stamp+' — كركوك';if(year)year.textContent=String(now.getFullYear());
 const menu=$('#menuBtn'),nav=$('#mainNav');
 menu?.addEventListener('click',()=>{const open=nav.classList.toggle('open');menu.setAttribute('aria-expanded',String(open));menu.textContent=open?'✕ إغلاق':'☰ القائمة'});
 nav?.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{nav.classList.remove('open');menu?.setAttribute('aria-expanded','false');if(menu)menu.textContent='☰ القائمة';nav.querySelectorAll('a').forEach(x=>x.classList.toggle('active',x===a))}));
 const form=$('#siteSearch'),input=$('#searchInput');let status=null;
 const searchable=$$('.news-card,.wide-card,.report-grid article,.latest article,.important li,.photo-grid img,.city-list a');
 const search=()=>{const q=(input?.value||'').trim().toLocaleLowerCase('ar');let count=0;searchable.forEach(el=>{const ok=!q||el.textContent.toLocaleLowerCase('ar').includes(q)||((el.getAttribute('alt')||'').toLocaleLowerCase('ar').includes(q));el.hidden=!ok;if(ok)count++});if(!status&&form){status=document.createElement('p');status.className='search-status';status.setAttribute('role','status');form.insertAdjacentElement('afterend',status)}if(status)status.textContent=q?'نتائج البحث عن «'+q+'»: '+count+' مادة':'تم عرض جميع المواد';};
 form?.addEventListener('submit',e=>{e.preventDefault();search();status?.scrollIntoView({behavior:'smooth',block:'nearest'})});
 input?.addEventListener('input',()=>{if(!input.value.trim()){searchable.forEach(el=>el.hidden=false);if(status)status.textContent=''}});
 input?.addEventListener('keydown',e=>{if(e.key==='Escape'){input.value='';searchable.forEach(el=>el.hidden=false);if(status)status.textContent=''}});
 const track=$('#tickerTrack');if(track&&!track.dataset.clone){track.innerHTML+=track.innerHTML;track.dataset.clone='1'}
 $$('img').forEach(img=>img.addEventListener('error',()=>{if(img.dataset.failed)return;img.dataset.failed='1';img.src='assets/news-placeholder.svg'}));
 const top=document.createElement('button');top.type='button';top.className='back-top';top.textContent='↑';top.setAttribute('aria-label','العودة إلى أعلى الصفحة');document.body.appendChild(top);const update=()=>top.classList.toggle('visible',window.scrollY>420);window.addEventListener('scroll',update,{passive:true});top.addEventListener('click',()=>window.scrollTo({top:0,behavior:'smooth'}));update();
});
})();